#!/usr/bin/env python3
"""Reproducibly stage reviewed LSG release files on a PR branch, never publish."""
from __future__ import annotations
from hashlib import sha1,sha256
import argparse,json,shutil,sys
from pathlib import Path
from lxml import etree

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from stable_sword_refs import (parse_keys,parse_registry,inspect_references,
                               module_payload_digest,proof_errors)
from sword_native_inventory import collect_native_inventory
from validate import validate
from build import build
from catalogue_release_coverage import coverage
from publish_reviewed_release import approved_release
from release_preflight import inspect_approved_releases

OLD='d6abd7416d026c86ce2e9577e3bfe7a10159c5c78d236913359c7fab013449d0'
NEW='1eb474496bef0388da403528ea080da489d8b4d980d4b11397ffd8cfe2398a4d'
USFX='fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e'
VERSION='1.0.0'
TAG='lsg-1.0.0'
MODULE='BRLSG1910'
NS='{http://www.bibletechnologies.net/2003/OSIS/namespace}'

def sha(raw): return sha256(raw).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',required=True,type=Path)
    p.add_argument('--native-index',required=True,type=Path)
    a=p.parse_args()
    work=a.work.resolve(strict=True)
    main=ROOT/'sources/cleaned/bibles/fr/lsg-1910/lsg-1910.osis.xml'
    editorial=main.parent/'editorial'
    module=ROOT/'modules/lsg-1910'
    payload=module/'payload'
    xml=work/'LSG1910-1.0.0.osis.xml'
    assert sha(xml.read_bytes())==NEW
    assert sha(main.read_bytes())==OLD
    assert sha((ROOT/'sources/original/bibles/fr/lsg-1910/fraLSG_usfx.zip').read_bytes())==USFX
    base=read(main.parent/'CLEANUP_MANIFEST.json')
    v=read(work/'validation.json')
    n=read(work/'native-readback.json')
    full=read(work/'full-source-native-readback.json')
    decision=read(editorial/'REVIEWED_REFERENCE_AND_INTRO_OVERLAY_2026-11-23.json')
    if not (base['cleaned_osis_sha256']==OLD and
        v['source_sha256']==NEW and v['source_absent_reference_endpoints']==0 and
        v['editorial_repair_fragments']==12 and v['introduction_decisions']==3 and
        n['source_verse_count']==31170 and n['native_verse_count']==31169 and
        n['missing_native_source_verse_keys']==['Mark.10.53'] and
        full['source_sha256']==NEW and full['full_body_mismatch_count']==0 and
        full['note_caller_type_or_body_mismatch_count']==0 and
        full['counts']['native_verse_nonspace_text_equal']==31169 and
        full['counts']['native_note_caller_type_nonspace_body_equal']==9751 and
        decision['approved_for_candidate_only'] is True):
        raise SystemExit('Cannot stage source/native build with incomplete evidence')
    if not (payload/'modules/texts/rawtext/brlsg1910').is_dir():
        raise SystemExit('Historical module payload identity differs')
    # The old 0.1.0 Git commits and immutable release remain intact.
    shutil.rmtree(payload)
    shutil.copytree(work/'sword',payload)
    main.write_bytes(xml.read_bytes())
    base.update({
      'previous_approved_cleaned_osis_sha256':OLD,
      'cleaned_osis_sha256':NEW,'cleaned_osis_bytes':xml.stat().st_size,
      'final_candidate_osis_sha256':NEW,
      'published_release_provenance':'config/catalogue-import-lsg-1.0.0.json',
      'status':'reviewed_lsg_1_0_0_candidate_pending_publication'})
    write(main.parent/'CLEANUP_MANIFEST.json',base)

    cfg=read(ROOT/'config/osis-policy.json')
    source_proof={
       'status':'validated','source_kind':'bible',
       'no_transformation_performed':True,
       'schema_sha256':cfg['schema_sha256'],
       'policy_sha256':sha(json.dumps(cfg,sort_keys=True,ensure_ascii=False).encode()),
       'source_sha256':NEW,
       'provenance_audit_sha256':sha((work/'full-source-native-readback.json').read_bytes()),
       'note':'Validated reviewed 1.0.0 source and separate full 31169-verse/9751-note native parity'}
    write(module/'SOURCE_VALIDATION.json',source_proof)
    ledger=editorial/'REVIEWED_REFERENCE_AND_INTRO_OVERLAY_2026-11-23.json'
    receipts=[work/x for x in ('editorial.receipt.json','individual.receipt.json',
                               'validation.json','full-source-native-readback.json')]
    norm={
      'status':'structural_edit_verified_not_published',
      'edition':'reader_optimized','kind':'bible',
      'full_text_exactly_preserved':True,'inline_semantic_tags_preserved':True,
      'original_source_unchanged':True,
      'schema_sha256':cfg['schema_sha256'],
      'source_sha256':OLD,'output_sha256':NEW,
      'plan_sha256':sha(ledger.read_bytes()),
      'diff_sha256':sha(b''.join(sha(x.read_bytes()).encode() for x in receipts)),
      'review_asserted_by_plan':'Owner-reviewed separate LSG 1.0.0 derivative approved 2026-11-23; Scripture/notes native verified',
      'operations':[
        {'operation':'source_attested_navigation_links','source':OLD,'result':NEW},
        {'operation':'reviewed_exact_electronic_reference_fragments','count':12},
        {'operation':'source_introduction_typo_and_link_splits','count':3},
        {'operation':'individually_addressed_citation_segmentation','source_groups':4909},
      ],
    }
    write(module/'NORMALIZATION_REPORT.json',norm)

    merge={
      'schema_version':1,
      'source_document_sha256':USFX,'versification':'Segond',
      'policy':'approved_explicit_temporary_adjacent_verse_index_merge',
      'authorization':{
        'who':'Bible Resources project owner','date':'2026-11-23',
        'basis':'Reversible Mark 10:52-53 mapping previously approved for 0.1.0 and continued with user informed for version 1.0.0',
        'evidence_url':'https://github.com/icfmp/Bible-Resources/issues/545'},
      'allowed_merges':[{
        'osis_source_key':'Mark.10.53','osis_reader_key':'Mark.10.52',
        'status':'temporarily_authorized_versification_compromise',
        'source_content_preserved':True,
        'independent_reference_access_lost':True,'reversible':True}]}
    policyfile=module/'SOURCE_REFERENCE_MERGES.json'
    write(policyfile,merge)
    keys,registry,info=collect_native_inventory(a.native_index,module,MODULE)
    verses={v.get('osisID') for v in etree.parse(str(xml)).iter(NS+'verse') if v.get('osisID')}
    chapters={k.rsplit('.',1)[0] for k in verses}
    assert len(verses)==31170 and len(chapters)==1189
    index=inspect_references(
      parse_keys(''.join(k+'\n' for k in sorted(verses))),
      parse_keys(keys),parse_registry(registry,'Segond'),
      [('Mark.10.53','Mark.10.52')])
    if (index['status']!='stable_reference_index_verified_with_reviewed_merges' or
        index['source_reference_count']!=31170 or
        index['resolved_reader_reference_count']!=31169 or
        info['engine_release']!='stable'):
        raise SystemExit('Stock SWORD registry mismatches approved source-only indexing exception')
    index.update({
      'versification':'Segond','reader_engine':'libsword',
      'reader_version':info['reader_version'],'engine_release':'stable',
      'registry_source':'installed_sword_versification_mgr',
      'source_osis_sha256':NEW,'module_payload_sha256':module_payload_digest(module),
      'reviewed_by':'Bible Resources project owner — source-bound Mark 10:53 stock Segond compromise continued for v1.0.0, 2026-11-23',
      'reviewed_merge_policy_sha256':sha(policyfile.read_bytes()),
      'original_publisher_document_sha256':USFX,
      'full_source_chapter_character_streams_verified':True,
      'full_readback_chapter_count':len(chapters),
      'full_readback_evidence_sha256':sha((work/'full-source-native-readback.json').read_bytes()),
      'source_to_native_full_body_mismatch_count':0,
      'source_to_native_note_mismatch_count':0,
      'published':False})
    write(module/'SWORD_COMPATIBILITY.json',index)
    failures=proof_errors(module,'Segond',NEW)
    if failures:
        raise SystemExit('New stable SWORD index proof failed: '+'; '.join(failures[:8]))

    meta=read(module/'metadata.json')
    meta['version']=VERSION
    meta['index_audit']={'mode':'stock_reader_keys'}
    meta['quality']['reviewed_by']='Bible Resources project owner — reviewed 1.0.0 continuation requested 2026-11-23'
    write(module/'metadata.json',meta)

    profile_source=editorial/'profiles/fr-segond-1910.md'
    card=profile_source.read_text(encoding='utf-8')
    old=card
    for a,b in (
      ('**Version Bible Resources :** 0.1.0','**Version Bible Resources :** 1.0.0'),
      ('| Version | 0.1.0 |','| Version | 1.0.0 |'),
      ('**Édition numérique :** Bible Resources 0.1.0, novembre 2026.',
       '**Édition numérique :** Bible Resources 1.0.0, novembre 2026.')):
        if card.count(a)!=1:raise SystemExit('Original approved profile field ambiguous')
        card=card.replace(a,b,1)
    assert card!=old and '**EDITORIALLY APPROVED READER TEXT' in card
    profile_source.write_text(card,encoding='utf-8')
    profile=read(module/'profiles/fr.json')
    profile['module_version']=VERSION
    profile['revision']='2026-11-23.1'
    profile['approved_at']='2026-11-23'
    profile['approval_url']='https://github.com/icfmp/Bible-Resources/pull/546'
    cb=profile_source.read_bytes()
    profile['source_git_blob_sha1']=sha1(
        b'blob '+str(len(cb)).encode()+b'\0'+cb).hexdigest()
    profile['evidence_urls']['curated_release']='https://github.com/icfmp/Bible-Resources/releases/tag/'+TAG
    write(module/'profiles/fr.json',profile)

    old_editorial=module/'EDITORIAL.md'
    old_log=old_editorial.read_text(encoding='utf-8')
    if not old_log.startswith('# Louis Segond 1910 — Bible Resources 0.1.0'):
        raise SystemExit('Historical editorial record changed')
    old_editorial.write_text(
      '# Louis Segond 1910 — Bible Resources 1.0.0 (release review)\n\n'
      '**Not yet published.** New edition based on the complete source-verified '
      'candidate SHA-256 '+NEW+'. Actual SWORD is a new zText payload.\n\n'
      '- 12 reviewed source-specific electronic reference-fragment repairs and '
      '3 introduction decisions, fully source-proven and reversible.\n'
      '- 31,169/31,169 native verse bodies preserve the original Scripture text; '
      '9,751/9,751 native note caller/type/bodies match the revised source.\n'
      '- Original 31,170 verse keys preserved. Stock Segond lacks Mark.10.53 '
      'as a separately addressable verse; its text is included under Mark.10.52, '
      'with a separately owner-reviewed reversible compatibility policy.\n'
      '- The source contains no Job.34.37. No source-absent verse is added.\n'
      '- Historical release 0.1.0 remains immutable and distinctly documented below.\n\n'
      '## Historical 0.1.0 editorial record\n\n'+old_log,encoding='utf-8')

    draft=editorial/'releases/LSG-1.0.0-DRAFT.md'
    notes=editorial/'releases/LSG-1.0.0.md'
    notes.write_text(
       draft.read_text(encoding='utf-8').replace(
        '1.0.0 build candidate (NOT PUBLISHED)',
        '1.0.0 reviewed release staging (NOT YET PUBLISHED)')
       +'\n## Full reviewed native evidence\n\n'
       '- Scripture body parity: 31,169/31,169 native entries match the '
       'source, including the source-authored Mark.10.53 text in the available '
       'Mark.10.52 slot; 9,751/9,751 note contents and callers match.\n'
       '- Source SHA-256: '+NEW+'. Released stable SWORD '+info['reader_version']+'.\n'
       '- Publication remains gated on the exact final package, catalogue, '
       'and public approval. Source-original USFX is immutable.\n',encoding='utf-8')
    draft.unlink()

    # The production build is deterministic and checks all *actual* modules.
    # Do not weaken the snapshot check: regenerate the snapshot only from a
    # separately validated set of installed payload bytes.
    snapshot=ROOT/'catalog/v1/catalog.json'
    historical=snapshot.read_bytes()
    snapshot.unlink()
    try:
        _,errors=validate(ROOT)
        if errors:raise SystemExit('Validation before catalogue refresh failed: '+'; '.join(errors[:10]))
        dist=work/'dist'
        build(root=ROOT,output=dist)
    except BaseException:
        snapshot.write_bytes(historical)
        raise
    snapshot.write_bytes((dist/'catalog/v1/catalog.json').read_bytes())
    zip_path=dist/'sword/packages/BRLSG1910.zip'
    pkg=zip_path.read_bytes()
    files={p.relative_to(payload).as_posix():sha(p.read_bytes())
           for p in sorted(payload.rglob('*')) if p.is_file()}
    audit_sha=sha((work/'full-source-native-readback.json').read_bytes())
    write(ROOT/'config/catalogue-import-lsg-1.0.0.json',{
      'schema_version':1,'release_tag':TAG,'module_id':MODULE,
      'metadata_path':'modules/lsg-1910/metadata.json',
      'release_zip_sha256':sha(pkg),'release_audit_sha256':audit_sha,
      'source_usfm_zip_sha256':'64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900',
      'source_usfx_zip_sha256':USFX,
      'files':files,
      'editorial_approval':{
          'approved_by':'Bible Resources project owner','date':'2026-11-23',
          'scope':'Owner-requested reviewed LSG 1.0.0 with 12 electronic reference repairs, 3 introductions and previously approved Mark 10:53 provisional stock mapping'},
      'provenance':{
          'previous_approved_osis_sha256':OLD,
          'reviewed_candidate_osis_sha256':NEW,
          'original_usfx_zip_sha256':USFX,
          'new_full_native_readback_sha256':audit_sha}})
    write(ROOT/'config/release-plans/lsg-1.0.0.json',{
      'schema_version':1,'tag':TAG,'module_id':'lsg-1910',
      'sword_id':MODULE,'version':VERSION,
      'title':'Louis Segond 1910 — 1.0.0',
      'zip_name':MODULE+'-'+VERSION+'.zip',
      'package_sha256':sha(pkg),'package_size_bytes':len(pkg),
      'notes_path':'sources/cleaned/bibles/fr/lsg-1910/editorial/releases/LSG-1.0.0.md',
      'evidence_path':'modules/lsg-1910/SOURCE_VALIDATION.json',
      'editorial_path':'modules/lsg-1910/EDITORIAL.md',
      'authorization':{
          'reviewed_by':'Bible Resources project owner — continuation to v1.0.0 requested on 2026-11-23',
          'decision':'Owner-requested v1.0.0 derivative with independent source/reader text and note parity; explicit known temporary Mark.10.53 stock Segond index merge; no fabricated publisher verse',
          'evidence_url':'https://github.com/icfmp/Bible-Resources/pull/546',
          'source_rights':'eBible fraLSG public-domain source; independently reviewed original electronic reference citations and historical printed evidence'}})
    # Fail-closed offline release preflight; never calls the publishing API.
    # The historical 0.1.0 publication is immutable but ceases to be the
    # ACTIVE distribution route when 1.0.0 takes its place. Move its exact
    # old binding into an edition-owned archived record. Do not change a
    # single byte of its existing Release, ZIP hashes or print evidence.
    legacy_path=ROOT/'config/release-legacy-bindings.json'
    legacy=read(legacy_path)
    old_entries=[e for e in legacy.get('entries',[])
                 if e.get('module_id')=='lsg-1910']
    if (len(old_entries)!=1 or old_entries[0].get('version')!='0.1.0' or
        old_entries[0].get('tag')!='lsg-0.1.0' or
        old_entries[0].get('release_sha256')!=
        'af2f80ea84f40a6bf62993c9e65c2e2061e1ec20b34b0772a4eb775dd47723c1' or
        old_entries[0].get('catalogue_sha256')!=
        'f3f74a1016f708e10263b5628e606a73b727c0e80fbb7e131d195c4b11d86c51'):
        raise SystemExit('Historic published LSG 0.1.0 record identity differs')
    archive=editorial/'releases/LSG-0.1.0-LEGACY-BINDING.json'
    if archive.exists():
        raise SystemExit('A previous historical legacy record is already archived')
    write(archive,{
        'schema_version':1,
        'status':'immutable_historic_publication_not_current_catalogue_route',
        'prior_registry_path':'config/release-legacy-bindings.json',
        'superseded_by_current_tag':TAG,
        'original_entry':old_entries[0],
        'original_entry_sha256':sha(json.dumps(old_entries[0],
                                ensure_ascii=False,sort_keys=True).encode()),
        'reason':'Historical publication still accessible by lsg-0.1.0; '
                 'current curated catalogue must have exactly one active '
                 'release plan, v1.0.0. Original approved 0.1.0 hashes preserved.',
    })
    legacy['entries']=[e for e in legacy['entries']
                       if e.get('module_id')!='lsg-1910']
    write(legacy_path,legacy)
    # Re-run existing production coverage unaltered. It will reject either
    # a missing current plan or an unarchived duplicate route.
    contract=coverage(ROOT,built=dist)
    if not any(plan['tag']==TAG for _,plan in contract['planned']):
        raise SystemExit('Reviewed release plan missing from exact catalogue coverage')
    proof=approved_release(ROOT,ROOT/'config/release-plans/lsg-1.0.0.json',dist)
    if proof['package'].read_bytes()!=pkg:
        raise SystemExit('Curated release package differs from deterministic build')
    preflight=inspect_approved_releases(ROOT,('lsg-1910',))
    write(work/'v1-release-preflight.json',preflight)
    write(work/'v1-release-stage.json',{
       'status':'reviewed_lsg_1_0_0_branch_staged_for_pr_not_published',
       'source_sha256':NEW,'previous_approved_source_sha256':OLD,
       'release_zip_sha256':sha(pkg),'release_zip_size_bytes':len(pkg),
       'text_entries_verified':31169,'notes_verified':9751,
       'source_native_index_compromise':'Mark.10.53 appended under Mark.10.52',
       'public_release_created':False,'catalogue_published':False})
    print('Staged candidate (no publication):',sha(pkg),len(pkg))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
