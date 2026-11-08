#!/usr/bin/env python3
"""Acquire source-backed context for explicit OpenBible modern-site identities.

This is a resource preparation tool, never application-time inference. It does
not equate a modern site with an ancient place or translate/summarize content.
"""
import argparse
from datetime import date
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import quote,urlencode,urlsplit

ROOT=Path(__file__).resolve().parents[1]
USER_AGENT='BibleResources/0.1 (https://github.com/icfmp/Bible-Resources; source validation)'
LANGUAGES=('en','fr')


class Plain(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)


def plain(value):
    parser=Plain();parser.feed(value)
    return ' '.join(' '.join(parser.parts).split())


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


class Sources:
    def __init__(self,cache,offline=False,refresh=False):
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True);self.offline=offline;self.refresh=refresh

    def bytes(self,url,limit=2*1024*1024):
        if urlsplit(url).scheme!='https':raise ValueError('HTTPS source required')
        path=self.cache/hashlib.sha256(url.encode()).hexdigest()
        if path.is_file() and (self.offline or not self.refresh):data=path.read_bytes()
        else:
            if self.offline:raise ValueError('Source is not cached')
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':USER_AGENT}),timeout=30) as response:
                data=response.read(limit+1)
            if len(data)>limit:raise ValueError('Source exceeds bounded download size')
            path.write_bytes(data)
        if len(data)>limit:raise ValueError('Cached source exceeds safe limits')
        return data

    def json(self,url):return json.loads(self.bytes(url))


def source_records(path,prefix):
    result={}
    with Path(path).open() as stream:
        for line in stream:
            value=json.loads(line);identifier=value.get('id','')
            if not re.fullmatch(prefix+'[0-9a-f]{6}',identifier) or identifier in result:raise ValueError('Invalid source identity')
            result[identifier]=value
    return result


def linked_sites(place,modern):
    """Only the source's explicit modern_basis_id → coordinate-source Q link."""
    sites={}
    for identification in place.get('identifications',[]):
        for resolution in identification.get('resolutions',[]):
            identifier=resolution.get('modern_basis_id')
            if identifier not in modern:continue
            source=modern[identifier].get('coordinates_source',{})
            qid=source.get('id','')
            if source.get('type')=='wikidata' and re.fullmatch(r'Q[1-9][0-9]*',qid):
                sites[identifier]=qid
    return sites


def permitted_license(url):
    value=urlsplit(url)
    return (value.scheme=='https' and value.netloc in ('creativecommons.org','www.creativecommons.org')
            and bool(re.fullmatch(r'/(?:licenses/(?:by|by-sa)/(?:1\.0|2\.0|2\.5|3\.0|4\.0)|publicdomain/zero/1\.0)/?',value.path)))


def photograph(sources,filename,captions=None):
    url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',prop='imageinfo',
        iiprop='url|size|extmetadata|sha1|mime|timestamp',iiurlwidth=960,titles='File:'+filename,format='json',formatversion=2))
    pages=sources.json(url)['query']['pages']
    if len(pages)!=1 or 'imageinfo' not in pages[0]:raise ValueError('Image source unavailable')
    page=pages[0];info=page['imageinfo'][0];meta=info.get('extmetadata',{})
    license_url=meta.get('LicenseUrl',{}).get('value','')
    if license_url.startswith('//'):license_url='https:'+license_url
    if license_url.startswith('http://creativecommons.org/'):license_url='https://'+license_url[7:]
    license_url=re.sub(r'/deed\.[a-z-]+/?$','/',license_url)
    if not permitted_license(license_url):raise ValueError('Image license not supported or not verified')
    image_url=info.get('thumburl','')
    if (urlsplit(image_url).scheme!='https' or urlsplit(image_url).hostname not in ('upload.wikimedia.org','thumb.wikimedia.org')
            or info.get('mime') not in ('image/jpeg','image/png','image/webp')):
        raise ValueError('Unsupported image origin/format')
    author=plain(meta.get('Artist',{}).get('value',''))
    license_name=plain(meta.get('LicenseShortName',{}).get('value',''))
    if not author or len(author)>2048 or not license_name:raise ValueError('Image attribution missing or exceeds safe limits')
    data=sources.bytes(image_url)
    return dict(url=image_url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),
        width=info['thumbwidth'],height=info['thumbheight'],pageid=page['pageid'],
        original_sha1=info['sha1'],commons_revision_timestamp=info['timestamp'],
        descriptionurl=info['descriptionurl'],author=author,license=license_name,license_url=license_url,
        caption=captions or {'und':filename},changes='Wikimedia thumbnail; original source caption/file title retained.')


def site_context(sources,qid,scope='coordinate-source-entity'):
    entity=sources.json('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json')['entities'][qid]
    if entity.get('id')!=qid or entity.get('type')!='item':raise ValueError('Wikidata identity mismatch')
    result=dict(wikidata=qid,wikidata_revision=entity['lastrevid'],scope=scope,
        labels={lang:entity['labels'][lang]['value'] for lang in LANGUAGES if lang in entity.get('labels',{})},
        descriptions={lang:entity['descriptions'][lang]['value'] for lang in LANGUAGES if lang in entity.get('descriptions',{})},
        source_url='https://www.wikidata.org/w/index.php?oldid='+str(entity['lastrevid']),
        introductions={},images=[],gaps=[])
    for language in LANGUAGES:
        link=entity.get('sitelinks',{}).get(language+'wiki')
        if not link:continue
        try:
            url='https://'+language+'.wikipedia.org/api/rest_v1/page/summary/'+quote(link['title'],safe='')
            article=sources.json(url)
            if article.get('wikibase_item')!=qid or article.get('type')!='standard':raise ValueError('Wikipedia identity ambiguous or mismatched')
            text=article.get('extract','')
            if not isinstance(text,str) or not text.strip():continue
            revision=article['revision']
            result['introductions'][language]=dict(text=text,language=language,name=article['title'],
                url='https://'+language+'.wikipedia.org/w/index.php?oldid='+str(revision),
                license='CC BY-SA 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                changes='Complete source-service introductory extract; no translation or generated summary.')
        except (OSError,ValueError,KeyError) as error:result['gaps'].append(dict(language=language,reason=str(error)))
    claims=entity.get('claims',{}).get('P18',[])
    for statement in claims:
        if len(result['images'])>=3:break
        if statement.get('rank')=='deprecated':continue
        value=statement.get('mainsnak',{}).get('datavalue',{}).get('value')
        if not isinstance(value,str):continue
        captions={}
        for qualifier in statement.get('qualifiers',{}).get('P2096',[]):
            caption=qualifier.get('datavalue',{}).get('value',{})
            if caption.get('language') in LANGUAGES:captions[caption['language']]=caption['text']
        try:result['images'].append(photograph(sources,value,captions))
        except (OSError,ValueError,KeyError) as error:result['gaps'].append(dict(image=value,reason=str(error)))
    return result


def build(ancient,modern,sources,identifiers,generation,source_inputs=None,identities=None):
    date.fromisoformat(generation)
    result=dict(schema=2,generation=generation,source='OpenBible.info explicit proposed modern-site identities',
        source_url='https://www.openbible.info/geo/',license_url='https://creativecommons.org/licenses/by/4.0/',
        database_terms='https://opendatacommons.org/licenses/odbl/1-0/',
        wikidata_license='CC0 1.0',wikidata_license_url='https://creativecommons.org/publicdomain/zero/1.0/',
        places={},sites={},ancient_contexts={},gaps=[],source_inputs=source_inputs or {},identity_registry=identities or {})
    for identifier in identifiers:
        if identifier not in ancient:raise ValueError('Unknown requested ancient ID: '+identifier)
        place=ancient[identifier];links=linked_sites(place,modern)
        result['places'][identifier]=dict(openbible_name=place['friendly_id'],modern_ids=sorted(links))
        reviewed=(identities or {}).get('ancient_places',{}).get(identifier)
        if reviewed:
            if reviewed['openbible_name']!=place['friendly_id'] or not reviewed.get('evidence'):raise ValueError('Reviewed source identity changed')
            result['ancient_contexts'][identifier]=site_context(sources,reviewed['wikidata'],'ancient-place')
        if not links and not reviewed:result['gaps'].append(dict(place=identifier,reason='No explicit source identity supplied'))
        for modern_id,qid in links.items():
            if modern_id in result['sites']:continue
            try:result['sites'][modern_id]=site_context(sources,qid)
            except (OSError,ValueError,KeyError) as error:result['gaps'].append(dict(place=identifier,modern=modern_id,reason=str(error)))
    result['coverage']=dict(requested_places=len(result['places']),modern_sites=len(result['sites']),
        places_with_context=sum(identifier in result['ancient_contexts'] or any(m in result['sites'] for m in p['modern_ids']) for identifier,p in result['places'].items()),
        source_languages=sorted({lang for site in (*result['sites'].values(),*result['ancient_contexts'].values()) for lang in site['introductions']}),
        photographs=sum(len(site['images']) for site in (*result['sites'].values(),*result['ancient_contexts'].values())))
    digest=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    result['revision']=generation+'.'+digest[:12]
    return result


def validate_dataset(data):
    """Fail publication closed; no source identity or license inferred here."""
    if len(data)>4*1024*1024:raise ValueError('Place context exceeds safe size')
    value=json.loads(data)
    if value.get('schema')!=2:raise ValueError('Unsupported place context schema')
    date.fromisoformat(value['generation'])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}',value['revision']):raise ValueError('Invalid revision')
    for identifier,place in value['places'].items():
        if not re.fullmatch(r'a[0-9a-f]{6}',identifier) or not place['openbible_name']:raise ValueError('Invalid ancient identity')
        if any(not re.fullmatch(r'm[0-9a-f]{6}',m) for m in place['modern_ids']):raise ValueError('Invalid modern identity')
    for scope,records in (('ancient-place',value['ancient_contexts']),('coordinate-source-entity',value['sites'])):
        for identifier,entry in records.items():
            if entry['scope']!=scope or not re.fullmatch(r'Q[1-9][0-9]*',entry['wikidata']):raise ValueError('Context identity scope mismatch')
            if scope=='ancient-place' and identifier not in value['identity_registry']['ancient_places']:raise ValueError('Ancient identity has no reviewed evidence')
            for language,intro in entry['introductions'].items():
                if intro['language']!=language or not intro['text'] or intro['license']!='CC BY-SA 4.0':raise ValueError('Invalid source introduction')
                if not re.fullmatch('https://'+re.escape(language)+r'\.wikipedia\.org/w/index\.php\?oldid=[0-9]+',intro['url']):raise ValueError('Introduction revision missing')
            for image in entry['images']:
                if not permitted_license(image['license_url']) or not image['author']:raise ValueError('Image attribution missing')
                if not re.fullmatch('[0-9a-f]{64}',image['sha256']) or not 0<image['bytes']<=2*1024*1024:raise ValueError('Image hash/size invalid')
    return value


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ids',nargs='+',required=True);p.add_argument('--generation',default=date.today().isoformat())
    p.add_argument('--offline',action='store_true');p.add_argument('--refresh',action='store_true');a=p.parse_args()
    sources=Sources(a.cache,a.offline,a.refresh);pins=json.loads((ROOT/'config/place-context-sources.json').read_text())
    inputs={}
    for name,item in pins['files'].items():
        data=sources.bytes(item['url'],item['limit'])
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('OpenBible input checksum mismatch')
        path=a.cache/(name+'.jsonl');path.write_bytes(data);inputs[name]=source_records(path,'a' if name=='ancient' else 'm')
    identities=json.loads((ROOT/'config/place-context-identities.json').read_text())
    value=build(inputs['ancient'],inputs['modern'],sources,sorted(set(a.ids)),a.generation,pins,identities)
    write_json(a.output,value);print(json.dumps(dict(coverage=value['coverage'],revision=value['revision'],gaps=value['gaps']),ensure_ascii=False))


if __name__=='__main__':main()
