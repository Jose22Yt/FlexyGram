import copy
import unittest
from compare_pair import compare,BASE,ALPHA
from tools.connected_alpha.performance.compare import ENVIRONMENT_KEYS

class CaptureGateTests(unittest.TestCase):
    def fixture(self,source=BASE):
        # Synthetic unit input exercising the parser contract; never saved as device evidence.
        env={k:'unit-fixture' for k in (*ENVIRONMENT_KEYS,'network_profile','sync_state','build_mode')}
        c={'frames':{'duration_ms':{'count':1,'median':7,'p95':7,'min':7,'max':7},'unbudgeted_frame_count':0,'frames':[], 'interval_ms_histogram':{'8.33333':1}},'health':{'eligible':True}}
        return {'schema':1,'evidence':'test_device','prepared_test_device':True,'source_commit':source,'package':ALPHA,'environment':env,'scenario':'dialogs_scroll','captures':[copy.deepcopy(c) for _ in range(20)]}
    def test_matching_fixture_parses_without_automatic_superiority(self):
        r=compare(self.fixture(),self.fixture('b'*40));self.assertTrue(r['comparable']);self.assertEqual(r['device_improvement'],'REQUIRES_REVIEW');self.assertIsNone(r['ttfd_ms'])
    def test_operation_evidence_is_rejected(self):
        a=self.fixture();a['evidence']='ISOLATED_OPERATION_COUNTS_NOT_DEVICE_TIMING';self.assertFalse(compare(a,self.fixture('b'*40))['comparable'])
    def test_wrong_source_identity_network_refresh_and_short_runs_are_rejected(self):
        for change in ['source','package','network','refresh','short']:
            a,b=self.fixture(),self.fixture('b'*40)
            if change=='source':a['source_commit']='c'*40
            if change=='package':b['package']='com.flexygram.messenger'
            if change=='network':b['environment']['network_profile']='different'
            if change=='refresh':b['captures'][0]['frames']['interval_ms_histogram']={'16.66667':1}
            if change=='short':b['captures']=b['captures'][:19]
            with self.subTest(change=change):self.assertFalse(compare(a,b)['comparable'])

if __name__=='__main__':unittest.main()
