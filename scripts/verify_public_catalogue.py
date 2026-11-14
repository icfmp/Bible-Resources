#!/usr/bin/env python3
"""Independently verify the ACTUAL published HTTPS catalogue and all ZIP bytes.

This is a generic post-deployment check for all approved resource types.
The source of truth is the committed, independently reviewed catalogue.
It does not rewrite or emit any Bible/commentary text. CDN delay is
handled with short bounded retries; failures are not marked successful.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urlunsplit, urlencode, parse_qsl
from urllib.request import Request, urlopen

MAX_ZIP_BYTES = 100 * 1024 * 1024
MAX_CATALOG_BYTES = 2 * 1024 * 1024
HEX = re.compile(r"[a-f0-9]{64}\Z")


class PublicDeliveryError(ValueError):
    """The publicly fetched content did not match the approved snapshot."""


def safe_source(url: str, base_url: str) -> None:
    """Public downloads must remain under the exact approved HTTPS origin."""
    if not isinstance(url, str) or not isinstance(base_url, str):
        raise PublicDeliveryError("Invalid public download origin")
    source = urlsplit(url)
    base = urlsplit(base_url)
    if (source.scheme != "https" or base.scheme != "https"
            or not source.netloc or source.netloc != base.netloc
            or source.username or source.password or source.query or source.fragment
            or base.username or base.password or base.query or base.fragment
            or not source.path.startswith(base.path.rstrip("/") + "/")):
        raise PublicDeliveryError("Non-canonical or external public release URL")


def public_url(url: str, *, attempt: int, run_id: str) -> str:
    """Cache-bust public CDN, without changing the original published URL."""
    p=urlsplit(url)
    return urlunsplit((p.scheme,p.netloc,p.path,
                       urlencode({"verify":run_id+"-"+str(attempt)}),""))


def read_public(url: str, *, limit: int, attempt: int, run_id: str) -> bytes:
    request = Request(public_url(url,attempt=attempt,run_id=run_id),
                      headers={"User-Agent":"Bible-Resources-ReleaseVerifier/1.0",
                               "Cache-Control":"no-cache"})
    with urlopen(request, timeout=24) as response:
        if (urlsplit(response.geturl()).netloc != urlsplit(url).netloc
                or urlsplit(response.geturl()).scheme != "https"):
            raise PublicDeliveryError("Unexpected cross-origin public redirect")
        data = response.read(limit+1)
    if len(data)>limit:
        raise PublicDeliveryError("Published resource exceeds safe size bounds")
    return data


def verify_one(expected: dict, base_url: str, *, attempt: int, run_id: str) -> list[str]:
    """Require public catalogue equality, then download and hash every ZIP."""
    url=base_url.rstrip("/")+"/catalog/v1/catalog.json"
    safe_source(url,base_url)
    data=read_public(url,limit=MAX_CATALOG_BYTES,attempt=attempt,run_id=run_id)
    actual=json.loads(data)
    if actual!=expected:
        raise PublicDeliveryError("Public catalogue differs from the reviewed Git snapshot")
    modules=expected.get("modules")
    if not isinstance(modules,list) or not modules:
        raise PublicDeliveryError("Approved public catalogue has no modules")
    done=[]
    for module in modules:
        info=module.get("download") or {}
        source=info.get("url")
        digest=info.get("sha256")
        size=info.get("size_bytes")
        if (not isinstance(source,str) or not isinstance(digest,str)
                or not HEX.fullmatch(digest) or type(size) is not int
                or not 0<size<=MAX_ZIP_BYTES):
            raise PublicDeliveryError("Unsafe or incomplete curated package metadata")
        safe_source(source,base_url)
        payload=read_public(source,limit=MAX_ZIP_BYTES,attempt=attempt,run_id=run_id)
        if len(payload)!=size or sha256(payload).hexdigest()!=digest:
            raise PublicDeliveryError(
                f"Public package hash/size mismatch for {module.get('sword_id','unknown')}"
            )
        done.append(str(module["sword_id"]))
    return done


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--base-url",default="https://icfmp.github.io/Bible-Resources/")
    p.add_argument("--attempts",type=int,default=6)
    p.add_argument("--pause-seconds",type=float,default=8.0)
    p.add_argument("--run-id",default="manual")
    args=p.parse_args()
    if (not 1<=args.attempts<=12 or not 0<=args.pause_seconds<=15
            or not re.fullmatch("[A-Za-z0-9_-]{1,48}",args.run_id)):
        raise SystemExit("Unsafe release verification bounds")
    expected=json.loads(args.snapshot.read_text(encoding="utf-8"))
    if expected.get("repository_url") != args.base_url.rstrip("/")+"/":
        raise SystemExit("Published origin disagrees with committed source")
    last=None
    for index in range(1,args.attempts+1):
        try:
            done=verify_one(expected,args.base_url,attempt=index,run_id=args.run_id)
            print("Verified live HTTPS catalogue and whole downloaded ZIP SHA-256 "
                  "for "+str(len(done))+" approved SWORD modules: "+", ".join(done))
            return 0
        except (PublicDeliveryError,OSError,TimeoutError,ValueError) as exc:
            last=exc
            if index<args.attempts:
                print(f"Public CDN not yet verified (attempt {index}/{args.attempts}); retrying")
                time.sleep(args.pause_seconds)
    raise SystemExit(f"Public deployment verification failed after bounded retries: {last}")


if __name__=="__main__":
    raise SystemExit(main())
