import unittest
from unittest.mock import patch
from pathlib import Path
from device_profile import matches_model
from fonts import label_font
class PublicTests(unittest.TestCase):
 def test_model_match(self):
  self.assertTrue(matches_model(0x0fe6,0x811e,' MHT-L1081 '))
  self.assertFalse(matches_model(0x0fe6,0x811e,'Another printer'))
  self.assertFalse(matches_model(0x0fe6,0x811e,'MHT-L10810'))
  self.assertFalse(matches_model(1,2,'MHT-L1081'))
 def test_portable_font(self):
  with patch('fonts.Path.is_file',return_value=False):
   font=label_font(24)
   self.assertGreater(font.getlength('Label'),0)
if __name__=='__main__':unittest.main()
