#!/usr/bin/env python3
"""Reversible, private, exact-byte repair of verified OSIS verse-group endpoints.

Input is one SHA-pinned OSIS edition plus an independently reviewed plan.
Only source machine attributes (opening @sID/@osisID/@n, paired closing @eID)
may change. All commentary text, notes, links, other markup and bytes remain
unchanged. Language/provider independent; never publishes source or SWORD.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path
import re
from xml.parsers import expat

from clean_source_osis import _tree, _load, _xml_tag_end, _local

BOOK = r"[1-4]?[A-Za-z][A-Za-z0-9]*"
START = re.compile(rf"^({BOOK})\.([1-9][0-9]*)\.([1-9][0-9]*)-([1-9][0-9]*)$")
ATTR = re.compile(rb'(?<![\w:.-])(?P<name>osisID|sID|eID|n)\s*=\s*(?P<q>["\x27])(?P<value>[^"\x27]*)(?P=q)')
MAX_EDITS = 100


class MilestoneRepairError(ValueError):
    pass


def _validated_plan(raw: bytes, plan: dict):
    if (not isinstance(plan, dict) or plan.get("schema_version") != 1
            or plan.get("status") != "RESEARCH_ONLY_PRIVATE_MILESTONE_CORRECTIONS"
            or sha256(raw).hexdigest() != plan.get("source_sha256")
            or not isinstance(plan.get("edits"), list)
            or not 1 <= len(plan["edits"]) <= MAX_EDITS):
        raise MilestoneRepairError("Unpinned or unreviewed source-geometry plan")
    targets = {}
    common={"old_sid","original_line","source_witness"}
    for op in plan["edits"]:
        if not isinstance(op,dict):
            raise MilestoneRepairError("Malformed source milestone edit")
        endpoint=(set(op)==common|{"new_end_verse"})
        shared=(set(op)==common|{"new_start_verse","overlap_predecessor_sid"})
        if (not (endpoint or shared)
                or type(op["original_line"]) is not int
                or op["original_line"] < 1
                or not isinstance(op["source_witness"],str)
                or not op["source_witness"].startswith("https://")
                or len(op["source_witness"]) > 500):
            raise MilestoneRepairError("Unattested source machine-only range correction")
        sid=op["old_sid"]
        m=START.fullmatch(sid) if isinstance(sid,str) else None
        if not m or sid in targets:
            raise MilestoneRepairError("Repeated or unparseable original verse group")
        book,chapter,a,b=m.groups()
        first,last=int(a),int(b)
        prefix=f"{book}.{chapter}."
        if endpoint:
            target=op["new_end_verse"]
            if type(target) is not int or not first <= target < last:
                raise MilestoneRepairError("Out-of-v11n endpoint repair must shrink range")
            revised_first,revised_last=first,target
        else:
            target=op["new_start_verse"]
            predecessor=op["overlap_predecessor_sid"]
            if (type(target) is not int or target!=first+1
                    or target>last or not isinstance(predecessor,str)
                    or predecessor==sid):
                raise MilestoneRepairError("Overlap repair must remove exactly one shared start verse")
            # A source-verified earlier group must actually claim the common
            # boundary. The original edition remains available unchanged.
            pred=predecessor.split(".",2)
            if len(pred)!=3 or pred[:2]!=[book,chapter]:
                raise MilestoneRepairError("Source overlap predecessor has different book/chapter")
            revised_first,revised_last=target,last
        original_ids=" ".join(prefix+str(i) for i in range(first,last+1))
        final_ids=" ".join(prefix+str(i) for i in range(revised_first,revised_last+1))
        expected_open={"sID":sid,"osisID":original_ids,"n":f"{first}-{last}"}
        revised_open={
            "sID":prefix+str(revised_first)+("-"+str(revised_last) if revised_first!=revised_last else ""),
            "osisID":final_ids,
            "n":str(revised_first)+("-"+str(revised_last) if revised_first!=revised_last else ""),
        }
        targets[sid]=(op,expected_open,revised_open)
    return targets


def repair_private_bytes(original: bytes, plan: dict) -> tuple[bytes,dict]:
    """Exact-bytes transformation. Only selected @attr values change."""
    if not isinstance(original,bytes) or not 100 <= len(original) <= 128*1024*1024:
        raise MilestoneRepairError("Unsafe or oversized private source")
    planned=_validated_plan(original,plan)
    source=_tree(original)
    by_node={}
    opening={}
    closing={}
    for node in source.iter():
        if not isinstance(node.tag,str) or _local(node)!="verse":
            continue
        sid=node.get("sID")
        eid=node.get("eID")
        if sid in planned:
            op, old, new=planned[sid]
            if (node.sourceline!=op["original_line"]
                    or any(node.get(name)!=value for name,value in old.items())
                    or node.get("eID") is not None
                    or len(node)):
                raise MilestoneRepairError("Exact source opener not attested")
            if sid in opening:
                raise MilestoneRepairError("Repeated target opener")
            opening[sid]=node
            by_node[node]=new
        if eid in planned:
            if (eid in closing or node.get("sID") is not None
                    or node.get("osisID") is not None or len(node)):
                raise MilestoneRepairError("Paired closing milestone is not unique")
            closing[eid]=node
            by_node[node]={"eID":planned[eid][2]["sID"]}
    if set(opening)!=set(planned) or set(closing)!=set(planned):
        raise MilestoneRepairError("Missing source opener or paired closer")
    # A repaired shared boundary must be confirmed against the earlier
    # authored source marker, not inferred from a numeric coincidence.
    all_starts={
        n.get("sID"):n for n in source.iter()
        if isinstance(n.tag,str) and _local(n)=="verse" and n.get("sID")
    }
    for sid,(op,_old,_new) in planned.items():
        if "new_start_verse" not in op:
            continue
        preceding=all_starts.get(op["overlap_predecessor_sid"])
        if preceding is None or preceding.sourceline>=opening[sid].sourceline:
            raise MilestoneRepairError("Missing earlier authored overlap predecessor")
        shared=sid.rsplit(".",1)[0]+"."+str(START.fullmatch(sid).group(3))
        predecessor_tokens=(preceding.get("osisID") or "").split()
        if (not predecessor_tokens or predecessor_tokens[-1]!=shared
                or preceding.get("n") is None
                or shared not in predecessor_tokens):
            raise MilestoneRepairError("Proposed overlap repair does not remove a real shared boundary")


    # Independently map lxml element identities to original lexical byte offsets.
    nodes=(node for node in source.iter() if isinstance(node.tag,str))
    parser=expat.ParserCreate(namespace_separator="}")
    touched=set()
    patches=[]
    processed=[0]

    def start(name,_attrs):
        node=next(nodes,None)
        processed[0]+=1
        translated="{"+name if "}" in name else name
        if node is None or node.tag!=translated:
            raise MilestoneRepairError("OSIS parser order differs from original bytes")
        replacements=by_node.get(node)
        if replacements is None:
            return
        pos=parser.CurrentByteIndex
        end=_xml_tag_end(original,pos)
        tag=original[pos:end]
        if not tag.endswith(b"/>"):
            raise MilestoneRepairError("Expected self-closing verse milestone")
        found={}
        for item in ATTR.finditer(tag):
            key=item.group("name").decode("ascii")
            if key in found:
                raise MilestoneRepairError("Duplicate target marker attribute")
            found[key]=item
        for key,new_value in replacements.items():
            match=found.get(key)
            if match is None or match.group("value").decode("utf-8") != node.get(key):
                raise MilestoneRepairError("Original machine attribute bytes differ")
            startpos=pos+match.start("value")
            endpos=pos+match.end("value")
            patches.append((startpos,endpos,new_value.encode("utf-8")))
        touched.add(node)

    def deny(*_args):
        raise MilestoneRepairError("OSIS DTD/entity declarations are disallowed")

    parser.StartElementHandler=start
    parser.StartDoctypeDeclHandler=deny
    parser.EntityDeclHandler=deny
    parser.ExternalEntityRefHandler=lambda *_args:0
    try:
        parser.Parse(original,True)
    except expat.ExpatError:
        raise MilestoneRepairError("Original lexical XML parsing failed") from None
    if touched != set(by_node) or next(nodes,None) is not None:
        raise MilestoneRepairError("Original lexical element coverage incomplete")
    if len(patches)!=4*len(planned):
        raise MilestoneRepairError("Expected exactly four attribute edits per range")
    patched=bytearray()
    offset=0
    for first,last,value in sorted(patches):
        if not offset<=first<last<=len(original):
            raise MilestoneRepairError("Overlapping machine attribute changes")
        patched.extend(original[offset:first])
        patched.extend(value)
        offset=last
    patched.extend(original[offset:])
    candidate=bytes(patched)
    revised=_tree(candidate)

    # Verify element order, every text/tail, and every other original attribute.
    count=0
    before=source.iter()
    after=revised.iter()
    for prior,now in zip_longest(before,after):
        if prior is None or now is None or prior.tag!=now.tag:
            raise MilestoneRepairError("Source XML element topology changed")
        if prior.text!=now.text or prior.tail!=now.tail:
            raise MilestoneRepairError("Actual authored text/notes/tails changed")
        expected=dict(prior.attrib)
        expected.update(by_node.get(prior,{}))
        if expected!=dict(now.attrib):
            raise MilestoneRepairError("Unreviewed OSIS metadata difference")
        count+=1
    if count < 3:
        raise MilestoneRepairError("Unreasonably small OSIS source tree")
    return candidate,{
        "status":"PRIVATE_VERIFIED_BYTE_LOCAL_MILESTONE_PREVIEW_NOT_PUBLISHED",
        "source_sha256":sha256(original).hexdigest(),
        "candidate_sha256":sha256(candidate).hexdigest(),
        "source_xml_element_count":count,
        "corrected_source_verse_groups":len(planned),
        "original_machine_attribute_values_replaced":len(patches),
        "removed_invalid_verse_assignments":sum(
            int(START.fullmatch(x).group(4))-op[0]["new_end_verse"]
            for x,op in planned.items() if "new_end_verse" in op[0]),
        "resolved_single_verse_overlap_assignments":sum(
            1 for op in planned.values() if "new_start_verse" in op[0]),
        "edited_original_bytes_outside_exact_machine_attribute_values":False,
        "all_source_text_notes_links_and_other_markup_identical":True,
        "historical_edition_collation_complete":False,
        "editorial_approval_for_publication":False,
        "original_text_or_module_released":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--sha256",required=True)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--private-output",type=Path,required=True)
    args=parser.parse_args()
    original=_load(args.source,args.sha256)
    if (args.plan.is_symlink() or not args.plan.is_file()
            or args.plan.stat().st_size>100000):
        parser.error("Untrusted private source repair plan")
    plan=json.loads(args.plan.read_text("utf-8"))
    if (args.private_output.exists() or args.private_output.is_symlink()
            or not args.private_output.parent.is_dir()
            or args.private_output.resolve()==args.source.resolve()):
        parser.error("Refuse to overwrite original or private candidate")
    candidate,receipt=repair_private_bytes(original,plan)
    args.private_output.write_bytes(candidate)
    print(json.dumps(receipt,sort_keys=True))


if __name__=="__main__":
    main()
