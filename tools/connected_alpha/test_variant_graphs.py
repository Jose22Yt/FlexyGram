"""Reject cross-variant or absent signing guards in the actual-graph checker."""
from pathlib import Path
import importlib.util,unittest
P=Path(__file__).resolve().parents[1]/'work1/check_variant_graphs.py'
spec=importlib.util.spec_from_file_location('variant_graph_guard',P);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class VariantGraphs(unittest.TestCase):
 def logs(self):return guard.ALPHA+' SKIPPED\n:TMessagesProj:assembleConnectedAlpha SKIPPED\n',guard.BETA+' SKIPPED\n:TMessagesProj:assembleBeta SKIPPED\n'
 def test_valid_graphs_still_allow_shared_native_prebuild(self):
  a,b=self.logs();self.assertTrue(guard.verify(a+':TMessagesProj:preBetaBuild SKIPPED\n',b))
 def test_alpha_must_not_pull_the_beta_validator(self):
  a,b=self.logs()
  with self.assertRaises(ValueError):guard.verify(a+guard.BETA+' SKIPPED\n',b)
 def test_beta_must_not_pull_the_alpha_validator(self):
  a,b=self.logs()
  with self.assertRaises(ValueError):guard.verify(a,b+guard.ALPHA+' SKIPPED\n')
 def test_guards_cannot_be_absent_or_only_mentioned_in_warnings(self):
  a,b=self.logs()
  for broken_a,broken_b in [(a.replace(guard.ALPHA+' SKIPPED','WARNING '+guard.ALPHA),b),(a,b.replace(guard.BETA+' SKIPPED','WARNING '+guard.BETA))]:
   with self.assertRaises(ValueError):guard.verify(broken_a,broken_b)
if __name__=='__main__':unittest.main()
