"""Exercise generated trace SQL against concrete samples, not string matching."""
import sqlite3,unittest
from performance.perfetto import plan
from performance.metrics import summary
class Measurements1280(unittest.TestCase):
 def test_surface_quantiles_are_nearest_rank_and_exclude_other_processes(self):
  c=sqlite3.connect(':memory:')
  c.executescript('CREATE TABLE actual_frame_timeline_slice(upid INTEGER,dur INTEGER);CREATE TABLE process(upid INTEGER,name TEXT);')
  c.execute('INSERT INTO process VALUES(1,?)',('io.github.jose22yt.flexygram.alpha',));c.execute("INSERT INTO process VALUES(2,'other.app')")
  c.executemany('INSERT INTO actual_frame_timeline_slice VALUES(1,?)',[(x*1000000,)for x in range(1,1001)])
  c.execute('INSERT INTO actual_frame_timeline_slice VALUES(2,999999999)');c.execute('INSERT INTO actual_frame_timeline_slice VALUES(1,-1)')
  sql=plan('io.github.jose22yt.flexygram.alpha')['frame_quantiles_sql']
  self.assertEqual((1000,500.0,950.0,990.0),c.execute(sql).fetchone())
  c.execute('DELETE FROM actual_frame_timeline_slice');self.assertEqual((0,None,None,None),c.execute(sql).fetchone())
 def test_summary_p99_uses_original_raw_samples(self):
  self.assertEqual(990,summary(list(range(1,1001)))['p99']);self.assertIsNone(summary([])['p99'])
if __name__=='__main__':unittest.main()
