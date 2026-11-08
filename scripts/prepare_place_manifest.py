#!/usr/bin/env python3
"""Pin a previously committed place dataset for GitHub-hosted distribution."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
from build_place_context import validate_dataset,ROOT,write_json


def prepare(source,root=ROOT):
    if not re.fullmatch('[0-9a-f]{40}',source):raise ValueError('Full source commit required')
    path='datasets/place-context-v2.json'
    data=subprocess.check_output(['git','show',source+':'+path],cwd=root)
    if data!=(root/path).read_bytes():raise ValueError('Commit the new dataset before pinning its distribution manifest')
    value=validate_dataset(data)
    entry=dict(revision=value['revision'],generation=value['generation'],sha256=hashlib.sha256(data).hexdigest(),
               size=len(data),format='bible-place-context-v2',
               url='https://raw.githubusercontent.com/icfmp/Bible-Resources/'+source+'/'+path)
    return dict(schema=1,resources={'place-context':entry})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);a=p.parse_args()
    write_json(ROOT/'datasets/place-context-catalogue.json',prepare(a.source))


if __name__=='__main__':main()
