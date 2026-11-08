"""Source identity, language and license checks for the offline place dataset."""
from copy import deepcopy
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_place_context import build,linked_sites,site_context,photograph,validate_dataset
from build import build as publish


class PlaceContextTests(unittest.TestCase):
    def test_coordinates_are_not_ancient_identity_and_name_matching_is_not_used(self):
        ancient={'a111111':dict(friendly_id='Synthetic ancient name',identifications=[dict(resolutions=[dict(modern_basis_id='m222222')])])}
        modern={'m222222':dict(friendly_id='Other name',coordinates_source=dict(type='wikidata',id='Q123'))}
        self.assertEqual(linked_sites(ancient['a111111'],modern),{'m222222':'Q123'})
        entry=dict(scope='coordinate-source-entity',wikidata='Q123',introductions={'en':{}},images=[])
        with patch('build_place_context.site_context',return_value=entry):
            value=build(ancient,modern,None,['a111111'],'2026-11-08')
        self.assertEqual(value['ancient_contexts'],{})
        self.assertEqual(value['sites']['m222222']['scope'],'coordinate-source-entity')
        modern['m222222']['coordinates_source']={}
        with patch('build_place_context.site_context',side_effect=AssertionError('No name lookup')):
            value=build(ancient,modern,None,['a111111'],'2026-11-08')
        self.assertEqual(value['coverage']['places_with_context'],0)

    def test_source_language_and_complete_extract_are_preserved_but_mismatched_article_is_rejected(self):
        entity=dict(id='Q123',type='item',lastrevid=42,labels={},descriptions={},claims={},
                    sitelinks={'enwiki':{'title':'First'},'frwiki':{'title':'Deuxième'}})
        english=dict(wikibase_item='Q999',type='standard',extract='Wrong source entity',title='First',revision=1)
        french=dict(wikibase_item='Q123',type='standard',extract='Texte original complet. Deuxième phrase.',title='Deuxième',revision=2)
        class Sources:
            def json(self,url):return {'entities':{'Q123':entity}} if 'wikidata.org' in url else english if 'en.wikipedia.org' in url else french
        value=site_context(Sources(),'Q123')
        self.assertEqual(list(value['introductions']),['fr'])
        self.assertEqual(value['introductions']['fr']['text'],french['extract'])
        self.assertIn('mismatched',value['gaps'][0]['reason'])

    def test_unlicensed_image_is_rejected_before_any_photo_download(self):
        class Sources:
            def json(self,url):return {'query':{'pages':[{'imageinfo':[{'extmetadata':{'LicenseUrl':{'value':'https://example.org/unknown'}}}]}]}}
            def bytes(self,url):raise AssertionError('Unknown license must not download')
        with self.assertRaisesRegex(ValueError,'license'):photograph(Sources(),'Synthetic.jpg')

    def test_real_sample_is_publishable_and_unknown_location_stays_empty(self):
        data=(ROOT/'datasets/place-context-v2.json').read_bytes();value=validate_dataset(data)
        self.assertEqual(value['places']['a1ad8e1']['modern_ids'],[])
        self.assertNotIn('a1ad8e1',value['ancient_contexts'])
        self.assertEqual(value['places']['a38ad9f']['modern_ids'],['m657590'])
        self.assertEqual(value['sites']['m657590']['scope'],'coordinate-source-entity')
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'site';publish(ROOT,output)
            manifest=json.loads((output/'place-context/v1/catalog.json').read_bytes())['resources']['place-context']
            self.assertEqual(manifest['sha256'],hashlib.sha256(data).hexdigest())
            self.assertEqual((output/'place-context/v1'/Path(manifest['url']).name).read_bytes(),data)
            self.assertEqual(json.loads((output/'catalog/v1/catalog.json').read_bytes())['modules'],[])
        bad=deepcopy(value);bad['sites']['m657590']['scope']='ancient-place'
        with self.assertRaises(ValueError):validate_dataset(json.dumps(bad).encode())
