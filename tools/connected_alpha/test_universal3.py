"""Real source boundaries and lab arithmetic; synthetic fixtures below are NOT physical results."""
import copy,json,re,subprocess,tempfile,unittest
from pathlib import Path
from performance.universal3 import distribution,grouped
from performance.universal_contract import BASE,ROOT,PRODUCTION,restore
from performance.compare import compare
from performance.scenarios import SCENARIOS
import test_performance
class Universal3(unittest.TestCase):
 def reports(self,device='a'*64):
  data=test_performance.PerformanceLab().reports()
  for report,label,sha in zip(data,['exteraless','alpha1275','candidate'],['1ad6a60a6834ffca722b1a22f4fba27ecb29a061',BASE,'c'*40]):
   report.update(label=label,source_commit=sha);report['environment'].update(device_pair_id=device,build_mode='release-profileable')
  return data
 def test_three_way_cohort_is_pinned_and_not_automatic_superiority(self):
  value=compare(self.reports(),'universal3');self.assertTrue(value['comparable']);self.assertEqual(value['superiority'],'NOT_AUTOMATICALLY_ESTABLISHED')
  for index in [0,1]:
   bad=self.reports();bad[index]['source_commit']='f'*40;self.assertFalse(compare(bad,'universal3')['comparable'])
  bad=self.reports();bad[2]['source_commit']=BASE;self.assertFalse(compare(bad,'universal3')['comparable'])
 def test_grouping_never_compares_fps_between_devices(self):
  value=grouped(self.reports()+self.reports('b'*64));self.assertTrue(value['comparable']);self.assertEqual(len(value['groups']),2);self.assertEqual(value['cross_device_fps_comparison'],'NOT_PERFORMED');self.assertEqual(value['universal_device_acceptance'],'NOT_ESTABLISHED');self.assertIsNone(value['first_useful_frame_ms'])
 def test_missing_cohort_per_device_cannot_qualify(self):
  value=grouped(self.reports()+self.reports('b'*64)[:-1]);self.assertFalse(value['comparable'])
 def test_old_guards_reject_thermal_refresh_cache_build_and_repetitions(self):
  mutations=[lambda r:r['environment'].update(cache_state='different'),lambda r:r['environment'].update(build_mode='debug'),lambda r:r['captures'].pop(),lambda r:r['captures'][0]['health'].update(eligible=False),lambda r:r.update(evidence='synthetic')]
  for mutate in mutations:
   bad=self.reports();mutate(bad[2]);self.assertFalse(grouped(bad)['comparable'])
 def test_private_or_unknown_identifiers_are_rejected_without_echo(self):
  for key,value in [('device_pair_id','private-serial'),('device_pair_id','phone 123'),('scenario','private chat'),('label','user@example.invalid')]:
   bad=self.reports()
   if key=='device_pair_id':bad[2]['environment'][key]=value
   else:bad[2][key]=value
   with self.assertRaises(ValueError)as error:grouped(bad)
   self.assertNotIn(value,str(error.exception))
 def test_raw_samples_required_and_frame_duration_not_touch_latency(self):
  good=grouped(self.reports());row=good['groups'][0]['rows'][0];self.assertEqual(row['pooled_frame_duration_ms']['count'],40);self.assertIsNone(row['touch_to_visible_ms']);self.assertIsNone(row['pooled_frame_duration_ms']['p99'])
  bad=self.reports();bad[1]['captures'][0]['frames']['frames']=[];self.assertFalse(grouped(bad)['comparable'])
 def test_p99_requires_1000_samples_and_rejects_invalid_values(self):
  self.assertIsNone(distribution(list(range(999)))['p99']);self.assertEqual(distribution(list(range(1,1001)))['p99'],990)
  for value in [True,-1,float('nan'),float('inf'),'secret']:
   with self.assertRaises(ValueError):distribution([value])
 def test_no_new_touch_automation_or_fixed_refresh_budget(self):
  self.assertTrue({'multitap','image_messages','stickers','typing','glass_on','glass_off','player_idle'}<=SCENARIOS.keys())
  source=(ROOT/'tools/connected_alpha/performance/capture.py').read_text();self.assertNotIn('shell\', \'input',source)
 def test_exact_production_deltas_reverse_and_reject_unknown_mutations(self):
  for path in PRODUCTION | {'tools/connected_alpha/test_performance2.py', 'tools/connected_alpha/test_alpha1275.py'}:
   data=(ROOT/path).read_bytes();before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT);self.assertEqual(restore(path,data),before)
   with self.assertRaises(ValueError):restore(path,data+b'\nUNREVIEWED\n')
   if path in PRODUCTION:self.assertEqual(before,subprocess.check_output(['git','show','1ad6a60a6834ffca722b1a22f4fba27ecb29a061:'+path],cwd=ROOT))
 def test_motion_remains_unapplied_and_patch_preserves_native_duration(self):
  path='TMessagesProj/src/main/java/org/telegram/ui/Components/ReplaceableIconDrawable.java';before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT);self.assertEqual((ROOT/path).read_bytes(),before)
  patch=ROOT/'tools/connected_alpha/performance/motion3.patch'
  with tempfile.TemporaryDirectory()as temp:
   target=Path(temp)/path;target.parent.mkdir(parents=True);target.write_bytes(before);subprocess.run(['git','apply',str(patch)],cwd=temp,check=True,capture_output=True);after=target.read_text();self.assertIn('animation.setDuration(150)',after);self.assertIn('removeAllUpdateListeners()',after)
   subprocess.run(['git','apply','--reverse',str(patch)],cwd=temp,check=True,capture_output=True);self.assertEqual(target.read_bytes(),before)
 def test_work1_and_identity_audit_remain_reserved(self):
  boundary=json.loads((ROOT/'tools/connected_alpha/performance/work1_boundary3.json').read_text());work1=set(boundary['work1_files']);self.assertFalse(work1&set(PRODUCTION))
  changed=set(subprocess.check_output(['git','diff','--name-only',boundary['work1_head']],cwd=ROOT,text=True).splitlines())
  from files_completion_contract import restore as restore_files, BASE as FILES_BASE, paths as files_paths
  for path in changed&work1:
   self.assertEqual(restore_files(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',FILES_BASE+':'+path],cwd=ROOT))
  actual={p for p in changed if p.startswith('TMessagesProj/')};self.assertEqual(actual-set(files_paths()),set(PRODUCTION)-set(files_paths()))
  for prefix in ['README.md','LICENSE','docs','TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/build.gradle','tools/connected_alpha/studio_contract.py']:
   if prefix=='TMessagesProj/build.gradle':
    from startup_contract import restore as restore_current
    self.assertEqual(restore_current(prefix,(ROOT/prefix).read_bytes()),subprocess.check_output(['git','show',BASE+':'+prefix],cwd=ROOT))
   else:self.assertEqual(subprocess.check_output(['git','diff',BASE,'--',prefix],cwd=ROOT),b'')
