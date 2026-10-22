"""Real host and exact native admission/binding/createView-loop excerpts; Android widgets remain doubles."""
from pathlib import Path
import unittest,subprocess,tempfile,os
import test_integration as integration
import presentation_fixtures
class PresentationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  old_write,old_harness=integration.write,integration.HARNESS
  try:
   integration.write=presentation_fixtures.write
   integration.HARNESS=Path(__file__).with_name('PresentationHarness.java')
   integration.IntegrationTests.setUpClass.__func__(cls)
  finally:integration.write, integration.HARNESS=old_write,old_harness
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def case(self,name):
  with tempfile.TemporaryDirectory() as d:
   p=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'org.telegram.ui.realalpha.local.PresentationHarness',name,d,str(self.library)],capture_output=True,text=True,env=dict(os.environ,FLEXYGRAM_HOST_UID=str(os.getuid())))
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   self.assertIn('HOST_LOCAL_INTEGRATION_NOT_ANDROID',p.stdout)
for case in ('sms','app','construction','binding','fragment','view','transition','cancelled','foreignRoot'):
 setattr(PresentationTests,'test_'+case,lambda self,c=case:self.case(c))
