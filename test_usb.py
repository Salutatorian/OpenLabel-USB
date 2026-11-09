import unittest
from unittest.mock import Mock
from usb_print import write_all
class TransportTests(unittest.TestCase):
 def test_partial_writes(self):
  writer=Mock(side_effect=[2,3]); self.assertEqual(write_all(b'abcde',writer),5)
  self.assertEqual([c.args[0] for c in writer.call_args_list],[b'abcde',b'cde'])
 def test_zero_write(self):
  with self.assertRaises(OSError):write_all(b'abc',lambda b:0)
 def test_bad_count(self):
  with self.assertRaises(OSError):write_all(b'abc',lambda b:4)
if __name__=='__main__':unittest.main()
