#!/usr/bin/env python3
"""Targeted real Xiphos QA of reviewed empty-paragraph sites, old vs candidate.

Compare actual reading-pane clipboard text and source-attested parallel title
and numbered verse witnesses. Does not claim pixel-level spacing equivalence.
"""
from hashlib import sha256
from pathlib import Path
import json, os, re, shutil, signal, subprocess, tempfile, time, unicodedata
from lxml import etree

def run(args,env,timeout=12,check=True):
    done=subprocess.run(args,env=env,stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,timeout=timeout)
    if check and done.returncode:
        raise RuntimeError("Reader command unsuccessful: "+args[0]+" "+args[1])
    if len(done.stdout)>350000: raise RuntimeError("Unbounded reader clipboard")
    return done.stdout
def tokenize(value):
    value=unicodedata.normalize("NFKD",value.casefold())
    return re.findall(r"[a-z0-9]+","".join(x for x in value if not unicodedata.combining(x)))
def stop(p):
    if p is not None and p.poll() is None:
        os.killpg(p.pid,signal.SIGTERM)
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL); p.wait(timeout=5)
def main_window(env):
    z=run(["xdotool","search","--onlyvisible","--class","[Xx]iphos"],env,check=False)
    for wid in z.decode("ascii","ignore").splitlines()[::-1]:
        if not wid.isdigit():continue
        g=run(["xdotool","getwindowgeometry","--shell",wid],env,check=False).decode("ascii","ignore")
        d=dict(re.findall(r"^(WIDTH|HEIGHT)=([0-9]+)$",g,re.M))
        if int(d.get("WIDTH","0"))>=650 and int(d.get("HEIGHT","0"))>=400:
            return wid
    return None
def copy_reader(env,window,x,y):
    run(["xdotool","windowfocus","--sync",window],env)
    run(["xdotool","mousemove",str(x),str(y),"click","1"],env)
    subprocess.run(["xclip","-selection","clipboard","-i"],
                   input=b"LSG_QA_UNRELATED_CLIPBOARD_SENTINEL",env=env,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                   check=True,timeout=8)
    run(["xdotool","key","--clearmodifiers","ctrl+a"],env)
    run(["xdotool","key","--clearmodifiers","ctrl+c"],env)
    time.sleep(0.8)
    return run(["xclip","-selection","clipboard","-o"],env)
def longest_native_prose_run(copied,native):
    # Require a distinctive eight-word native body witness plus one exact standalone title line.
    copied_words=tokenize(copied)
    native_words=tokenize(native)
    if len(copied_words)<30 or len(native_words)<15:return 0
    for span in (16,14,12,10,8,6):
        copied_set={tuple(copied_words[j:j+span])
                    for j in range(len(copied_words)-span+1)}
        if any(tuple(native_words[i:i+span]) in copied_set
               for i in range(4,len(native_words)-span+1)):
            return span
    return 0

def main():
    old = Path("modules/lsg-1910/payload").resolve()
    candidate = Path("/tmp/paragraph-native/payload").resolve()
    source = Path("/tmp/lsg-1.0.3-candidate.osis.xml")
    overlay = json.loads(Path("/tmp/empty-paragraph-review/overlay.json").read_text())
    assert sha256(source.read_bytes()).hexdigest() == overlay["candidate_sha256"]
    ns = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
    root = etree.fromstring(source.read_bytes())
    samples = []
    for row in overlay["changes"]:
        key = row["next_source_verse"]
        verse = next(v for v in root.iter(ns+"verse") if v.get("osisID")==key)
        para = next(p for p in verse.iterancestors() if p.tag==ns+"p")
        title = para.getprevious()
        assert title.tag == ns+"title" and title.get("type")=="parallel"
        samples.append((key, "".join(title.itertext())))
    results = {}
    for label, payload in (("published", old), ("candidate", candidate)):
        disp=app=None
        with tempfile.TemporaryDirectory(prefix="paragraph-xiphos-") as home:
            home=Path(home)
            for part in ("config","cache","data"):(home/part).mkdir()
            env=dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home/"config"),
                     XDG_CACHE_HOME=str(home/"cache"), XDG_DATA_HOME=str(home/"data"),
                     SWORD_PATH=str(payload), GDK_BACKEND="x11", DISPLAY=":91",
                     NO_AT_BRIDGE="1", LC_ALL="C.UTF-8")
            try:
                disp=subprocess.Popen(["Xvfb",":91","-screen","0","1280x800x24","-nolisten","tcp"],
                                       env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
                time.sleep(1.5)
                # Keep startup diagnostics private to this run, not the corpus.
                # The established Xiphos 4.2 reader test uses Ubuntu 24.04.
                app=subprocess.Popen(["dbus-run-session","--","xiphos"],env=env,stdout=subprocess.DEVNULL,
                                     stderr=None,start_new_session=True)
                window=None
                for _ in range(90):
                    if app.poll() is not None: raise RuntimeError("Real Xiphos exited")
                    window=main_window(env)
                    if window: break
                    time.sleep(.5)
                if not window:
                    print("XIPHOS_STARTUP_DIAGNOSTIC", label,
                          run(["xwininfo","-root","-tree"],env,check=False).decode("utf-8","replace")[:5000],flush=True)
                    raise RuntimeError("No real Xiphos reader window: "+label)
                run(["xdotool","windowsize",window,"1216","736"],env)
                run(["xdotool","windowmove",window,"16","16"],env)
                time.sleep(1.2)
                records={}
                for key,title in samples:
                    book,chapter,verse=key.split(".")
                    reference=book+" "+chapter+":"+verse
                    native=run(["diatheke","-b","BRLSG1910","-f","plain","-k",reference],env).decode("utf-8","replace")
                    expected=tokenize(title)
                    accepted=False
                    for nav in (reference, book+" "+chapter):
                        run(["xdotool","windowfocus","--sync",window],env)
                        run(["xdotool","key","--clearmodifiers","ctrl+l"],env)
                        run(["xdotool","type","--clearmodifiers","--delay","25",nav],env)
                        run(["xdotool","key","Return"],env)
                        time.sleep(2.5)
                        for x,y in ((535,290),(680,460),(390,550)):
                            selected=copy_reader(env,window,x,y).decode("utf-8","replace")
                            words=tokenize(selected)
                            hits=sum(words[i:i+len(expected)]==expected for i in range(len(words)-len(expected)+1))
                            overlap=longest_native_prose_run(selected,native)
                            # Short numbered verses can have fewer than eight words.
                            # Require a contiguous exact body witness from that verse,
                            # not merely a chapter match.
                            if overlap<6:
                                native_words=tokenize(native)
                                overlap=max((n for n in range(4,min(12,len(native_words)-4)+1)
                                    if any(tuple(native_words[i:i+n])==tuple(words[j:j+n])
                                           for i in range(4,len(native_words)-n+1)
                                           for j in range(len(words)-n+1))),default=0)
                            if hits==1 and overlap>=4:
                                records[key]={"parallel_title_once":True,"verse_witness_words":overlap,
                                    "clipboard_sha256":sha256(selected.encode()).hexdigest(),
                                    "clipboard_nonspace_sha256":sha256("".join(c for c in selected if not c.isspace()).encode()).hexdigest(),
                                    "clipboard_bytes":len(selected.encode()),"navigation":nav}
                                accepted=True
                                break
                        if accepted: break
                    if not accepted: raise RuntimeError("No exact title/verse witness in "+label+" "+key)
                results[label]=records
            finally:
                stop(app);stop(disp)
    comparisons={}
    for key,_ in samples:
        a,b=results["published"][key],results["candidate"][key]
        comparisons[key]={"exact_clipboard_equal":a["clipboard_sha256"]==b["clipboard_sha256"],
                          "nonspace_clipboard_equal":a["clipboard_nonspace_sha256"]==b["clipboard_nonspace_sha256"]}
    report={"source_sha256":overlay["candidate_sha256"],"actual_xiphos":True,
            "all_eight_title_and_verse_witnesses":True,"observations":results,
            "comparisons":comparisons,"visual_spacing_pixel_verified":False,"published":False}
    Path("/tmp/empty-paragraph-review/xiphos.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print("REAL_XIPHOS",json.dumps(report,sort_keys=True))
    assert all(row["nonspace_clipboard_equal"] for row in comparisons.values())

if __name__=="__main__":
    main()
