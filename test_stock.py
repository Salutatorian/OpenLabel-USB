import unittest
import tkinter as tk
from openlabel import App
class StockTests(unittest.TestCase):
 def test_stock_stays_four_by_six(self):
  t=tk.Tcl(); app=App.__new__(App)
  app.vars={k:tk.StringVar(master=t,value=v) for k,v in dict(width='40',height='20',gap='3',copies='1').items()}
  self.assertEqual(app.settings(),(101.6,152.4,3.0,1))
if __name__=='__main__':unittest.main()
