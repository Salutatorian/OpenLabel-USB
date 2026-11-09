import unittest
from PIL import Image
from label_core import make_job
class EncodingTests(unittest.TestCase):
 def test_pixels_padding_and_framing(self):
  im=Image.new('L',(9,1),255); im.putpixel((0,0),0); im.putpixel((8,0),0)
  job=make_job(im,40,20,3,1)
  self.assertIn(b'BITMAP 0,0,2,1,1,\x7f\x7f\r\nPRINT 1,1\r\n',job)
 def test_inversion(self):
  job=make_job(Image.new('L',(8,1),0),40,20,3,1,invert=True)
  self.assertIn(b'BITMAP 0,0,1,1,1,\xff\r\n',job)
 def test_reject_invalid(self):
  for args in [(float('nan'),20,3,1),(105,20,3,1),(40,20,3,0),(40,20,-1,1)]:
   with self.assertRaises(ValueError): make_job(Image.new('L',(8,1)),*args)
if __name__=='__main__': unittest.main()
