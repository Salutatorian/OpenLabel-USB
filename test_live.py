import tkinter as tk
import unittest
from unittest.mock import patch
from PIL import Image
from openlabel import App
class LiveTests(unittest.TestCase):
 def test_typing_selects_text_and_updates_preview(self):
  r=tk.Tk()
  try:
   with patch.object(App,'refresh'):a=App(r);r.update()
   a.imported=Image.new('L',(20,20))
   with patch.object(a,'preview',return_value=True) as preview:
    a.text.insert('end',' new text')
    r.after(250,r.quit);r.mainloop()
    self.assertIsNone(a.imported)
    self.assertTrue(preview.called)
   with patch.object(a,'preview',return_value=True) as preview:
    a.vars['font'].set('24');r.after(250,r.quit);r.mainloop()
    self.assertTrue(preview.called)
   def walk(w):
    for c in w.winfo_children():
     if 'text' in c.keys():self.assertNotEqual(c.cget('text'),'Update preview')
     walk(c)
   walk(r)
  finally:r.destroy()
if __name__=='__main__':unittest.main()
