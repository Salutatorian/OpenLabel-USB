import tkinter as tk
import unittest
from unittest.mock import patch
from openlabel import App
class LayoutTests(unittest.TestCase):
 def test_small_window_and_clean_labels(self):
  r=tk.Tk()
  try:
   with patch.object(App,'refresh'): a=App(r);r.geometry('400x520');r.update()
   self.assertLessEqual(r.minsize()[0],400)
   b=a.print_button
   self.assertGreater(b.winfo_height(),10)
   self.assertLessEqual(b.winfo_rooty()+b.winfo_height(),r.winfo_rooty()+r.winfo_height())
   def walk(w):
    for child in w.winfo_children():
     if 'text' in child.keys():self.assertTrue(str(child.cget('text')).isascii(),repr(child.cget('text')))
     walk(child)
   walk(r)
   self.assertTrue(hasattr(a,'controls_canvas'))
  finally:r.destroy()
if __name__=='__main__':unittest.main()
