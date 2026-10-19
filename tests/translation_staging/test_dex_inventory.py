import struct,unittest
from check_integration import dex_definitions
class DexInventoryTests(unittest.TestCase):
 def test_class_definitions_not_string_pool_mentions(self):
  value=b'Lsynthetic/Example;'
  data=bytearray(256);data[:8]=b'dex\n035\0'
  for offset,n in [(56,2),(60,112),(64,2),(68,120),(96,1),(100,128)]:struct.pack_into('<I',data,offset,n)
  # Two type mentions, only the second is actually defined.
  struct.pack_into('<II',data,112,200,230);struct.pack_into('<II',data,120,0,1);struct.pack_into('<I',data,128,1)
  data[200:200+len(value)+2]=bytes([len(value)])+value+b'\0'
  value2=b'Lsynthetic/Defined;';data[230:230+len(value2)+2]=bytes([len(value2)])+value2+b'\0'
  self.assertEqual(list(dex_definitions(data)),['Lsynthetic/Defined;'])
 def test_invalid_format_fails(self):
  with self.assertRaises(AssertionError):list(dex_definitions(b'not a dex'))
