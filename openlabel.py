"""OpenLabel: local label creation and independent TSPL printing."""
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
from label_core import make_job, validate
from usb_print import send_raw, devices
from fonts import label_font

class App:
    def __init__(self, root):
        self.root = root
        root.title('OpenLabel USB - Label studio')
        root.geometry('1060x780')
        root.minsize(360, 460)
        self.imported = None
        self.busy = False
        self.usb_paths = {}
        self.vars = {k: tk.StringVar(value=v) for k,v in
                     dict(width='101.6', height='152.4', gap='3', copies='1', font='36', printer='').items()}
        self.invert = tk.BooleanVar(value=False)
        style = ttk.Style()
        style.theme_use('clam')
        self.root.option_add('*tearOff',False)
        style.configure('TButton', padding=8)
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 23, 'bold'))
        outer = ttk.Frame(root, padding=12); outer.pack(fill='both', expand=True)
        footer = ttk.Frame(outer); footer.pack(side='bottom', fill='x', pady=(8,0))
        self.print_button=ttk.Button(footer,text='Print label...',command=self.print_label)
        self.print_button.pack(fill='x')
        self.status=ttk.Label(footer,text='Ready - 4 x 6 inches',wraplength=900)
        self.status.pack(anchor='w',fill='x',pady=(6,0))
        ttk.Label(outer, text='OpenLabel', style='Title.TLabel').pack(anchor='w')
        self.subtitle=ttk.Label(outer, text='Your labels. Your printer. All processing stays on this PC.',wraplength=900)
        self.subtitle.pack(anchor='w',fill='x', pady=(2,10))
        body = ttk.Frame(outer); body.pack(fill='both', expand=True)
        self.body=body
        self.controls_panel=ttk.Frame(body)
        self.controls_canvas=tk.Canvas(self.controls_panel,highlightthickness=0,width=320)
        scroll=ttk.Scrollbar(self.controls_panel,orient='vertical',command=self.controls_canvas.yview)
        scroll.pack(side='right',fill='y')
        self.controls_canvas.pack(side='left',fill='both',expand=True)
        self.controls_canvas.configure(yscrollcommand=scroll.set)
        controls = ttk.Frame(self.controls_canvas,padding=(0,0,8,8))
        self.controls=controls
        self.controls_window=self.controls_canvas.create_window((0,0),window=controls,anchor='nw')
        controls.bind('<Configure>',lambda e:self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox('all')))
        self.controls_canvas.bind('<Configure>',self.fit_controls)
        root.bind('<MouseWheel>',self.scroll_controls,add='+')
        root.bind('<FocusIn>',self.reveal_control,add='+')
        settings = ttk.LabelFrame(controls, text='Label stock', padding=12); settings.pack(fill='x')
        ttk.Label(settings, text='4 x 6 inches (101.6 x 152.4 mm)').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0,8))
        for row,(key,label) in enumerate([('gap','Gap (mm)'),('copies','Copies'),('font','Text size (points)')], start=1):
            ttk.Label(settings,text=label).grid(row=row,column=0,sticky='w',pady=4)
            ttk.Entry(settings,textvariable=self.vars[key],width=12).grid(row=row,column=1,padx=(15,0),pady=4)
        ttk.Label(controls,text='Type text or import a file').pack(anchor='w',pady=(18,5))
        self.text = tk.Text(controls,width=24,height=5,font=('Segoe UI',11),wrap='word')
        self.text.pack(fill='x'); self.text.insert('1.0','MY FIRST LABEL\nMade with OpenLabel')
        ttk.Button(controls,text='Import image or PDF...',command=self.load).pack(fill='x',pady=(12,4))
        self.source = ttk.Label(controls,text='Source: editable text',wraplength=300); self.source.pack(anchor='w',pady=8)
        ttk.Checkbutton(controls,text='Reverse bitmap polarity',variable=self.invert).pack(anchor='w')
        ttk.Label(controls,text='Connected USB printer').pack(anchor='w',pady=(12,4))
        self.printers = ttk.Combobox(controls,textvariable=self.vars['printer'],width=30,state='readonly')
        self.printers.pack(fill='x')
        ttk.Button(controls,text='Refresh printers',command=self.refresh).pack(fill='x',pady=4)
        actions = ttk.Frame(controls); actions.pack(fill='x')
        ttk.Button(actions,text='Save PNG...',command=lambda:self.export('png')).pack(side='left',expand=True,fill='x')
        ttk.Button(actions,text='Save print file...',command=lambda:self.export('prn')).pack(side='left',expand=True,fill='x',padx=(4,0))
        self.canvas=tk.Canvas(body,background='#e4e8eb',highlightthickness=0)
        self._layout_mode=None
        self._preview_timer=None
        body.bind('<Configure>',self.resize_layout)
        self.canvas.bind('<Configure>',self.schedule_preview)
        self._preview_error=False
        self.text.edit_modified(False)
        self.text.bind('<<Modified>>',self.text_changed)
        for key in ('font','gap','copies'):
            self.vars[key].trace_add('write',lambda *args:self.schedule_preview())
        self._refresh_timer=root.after(100,self.refresh)
        root.bind('<Destroy>',self.cancel_timers,add='+')
        self.schedule_preview()

    def cancel_timers(self,event):
        if event.widget is not self.root:return
        for timer in (self._preview_timer,self._refresh_timer):
            if timer is not None:
                try:self.root.after_cancel(timer)
                except tk.TclError:pass

    def text_changed(self,event=None):
        if not self.text.edit_modified():return
        self.text.edit_modified(False)
        self.imported=None
        self.source.config(text='Source: editable text')
        self.schedule_preview()

    def fit_controls(self,event):
        self.controls_canvas.itemconfigure(self.controls_window,width=max(1,event.width))
        self.source.configure(wraplength=max(100,event.width-20))

    def scroll_controls(self,event):
        widget=event.widget
        while widget is not None:
            if widget is self.controls_panel:
                self.controls_canvas.yview_scroll(-int(event.delta/120),'units')
                return 'break'
            widget=getattr(widget,'master',None)

    def reveal_control(self,event):
        widget=event.widget
        parent=widget
        while parent is not None and parent is not self.controls:
            parent=getattr(parent,'master',None)
        if parent is None:return
        self.root.update_idletasks()
        y=widget.winfo_rooty()-self.controls.winfo_rooty()
        top=self.controls_canvas.canvasy(0)
        bottom=top+self.controls_canvas.winfo_height()
        if y<top or y+widget.winfo_height()>bottom:
            self.controls_canvas.yview_moveto(max(0,y-12)/max(1,self.controls.winfo_height()))

    def resize_layout(self,event):
        width=self.root.winfo_width()
        self.subtitle.configure(wraplength=max(200,width-30))
        self.status.configure(wraplength=max(200,width-30))
        mode='stacked' if event.width<700 else 'side'
        if mode==self._layout_mode:return
        self._layout_mode=mode
        self.controls_panel.grid_forget();self.canvas.grid_forget()
        self.body.columnconfigure(0,weight=1 if mode=='stacked' else 0,minsize=0)
        self.body.columnconfigure(1,weight=0 if mode=='stacked' else 1)
        self.body.rowconfigure(0,weight=3 if mode=='stacked' else 1)
        self.body.rowconfigure(1,weight=2 if mode=='stacked' else 0)
        self.controls_panel.grid(row=0,column=0,sticky='nsew',padx=(0,0 if mode=='stacked' else 12))
        self.canvas.grid(row=1 if mode=='stacked' else 0,column=0 if mode=='stacked' else 1,sticky='nsew',pady=(8 if mode=='stacked' else 0,0))

    def schedule_preview(self,event=None):
        if self._preview_timer is not None:self.root.after_cancel(self._preview_timer)
        self._preview_timer=self.root.after(120,self.redraw_preview)

    def redraw_preview(self):
        self._preview_timer=None
        self.preview(quiet=True)

    def settings(self):
        width, height = 101.6, 152.4
        gap = float(self.vars['gap'].get())
        copies=int(self.vars['copies'].get()); validate(width,height,gap,copies)
        return width,height,gap,copies

    def render(self):
        width,height,_,_=self.settings()
        size=round(width*8),round(height*8)
        im=Image.new('L',size,255)
        margin=16
        if self.imported is not None:
            fitted=ImageOps.contain(self.imported,(size[0]-margin*2,size[1]-margin*2),Image.Resampling.LANCZOS)
            im.paste(fitted,((size[0]-fitted.width)//2,(size[1]-fitted.height)//2))
        else:
            points=float(self.vars['font'].get())
            if not 6<=points<=144: raise ValueError('Text size must be 6-144 points.')
            font=label_font(round(points*203/72))
            draw=ImageDraw.Draw(im); lines=[]
            for paragraph in self.text.get('1.0','end-1c').split('\n'):
                line=''
                for char in paragraph:
                    if draw.textlength(line+char,font=font)>size[0]-margin*2:
                        lines.append(line); line=''
                    line+=char
                lines.append(line)
            step=round(font.size*1.3)
            if len(lines)*step>size[1]-margin*2:
                raise ValueError('Text is too tall for this label. Reduce the text size to fit the 4 x 6 label.')
            for n,line in enumerate(lines): draw.text((margin,margin+n*step),line,font=font,fill=0)
        return im.point(lambda p:255 if p>=128 else 0)

    def preview(self,quiet=False):
        try:
            im=self.render()
            # The toggle adjusts the transport convention; preview shows intended ink.
            im.thumbnail((max(20,self.canvas.winfo_width()-48),max(20,self.canvas.winfo_height()-48)))
            self.photo=ImageTk.PhotoImage(im)
            self.canvas.delete('all')
            self.canvas.create_image(self.canvas.winfo_width()/2,self.canvas.winfo_height()/2,image=self.photo)
            if self._preview_error:
                self.status.config(text='Ready - 4 x 6 inches')
                self._preview_error=False
            return True
        except Exception as exc:
            self._preview_error=True
            self.canvas.delete('all')
            self.status.config(text=str(exc))
            if not quiet: messagebox.showerror('Check label settings',str(exc))
            return False

    def load(self):
        path=filedialog.askopenfilename(filetypes=[('Images and PDFs','*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.pdf')])
        if not path:return
        try:
            if Path(path).suffix.lower()=='.pdf':
                import pymupdf
                with pymupdf.open(path) as doc:
                    if doc.needs_pass: raise ValueError('Password-protected PDFs are not supported.')
                    if not len(doc): raise ValueError('PDF has no pages.')
                    rect=doc[0].rect
                    scale=min(203/72,2400/max(rect.width,rect.height))
                    pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(scale,scale),colorspace=pymupdf.csGRAY,alpha=False)
                    image=Image.frombytes('L',(pix.width,pix.height),pix.samples)
                    suffix=f' - page 1 of {len(doc)}'
            else:
                with Image.open(path) as src:
                    src=ImageOps.exif_transpose(src).convert('RGBA')
                    bg=Image.new('RGBA',src.size,'white'); bg.alpha_composite(src)
                    image=bg.convert('L'); suffix=''
            self.imported=image
            self.source.config(text='Source: '+Path(path).name+suffix)
            self.preview()
        except Exception as exc: messagebox.showerror('Could not open file',str(exc))

    def use_text(self):
        self.imported=None; self.source.config(text='Source: editable text'); self.preview()

    def refresh(self):
        try:
            paths=devices()
            self.usb_paths={f'MHT-L1081 USB ({i+1})':path for i,path in enumerate(paths)}
            self.printers.configure(values=list(self.usb_paths))
            self.vars['printer'].set(next(iter(self.usb_paths),''))
            if not paths:self.status.config(text='Printer not detected. Connect and power on your MHT-L1081, then refresh.')
            else:self.status.config(text='Direct USB ready. No Milestone printer queue is used.')
        except Exception as exc:
            self.usb_paths={}; self.vars['printer'].set('')
            self.status.config(text='USB discovery failed: '+str(exc))

    def export(self,kind):
        try:
            im=self.render()
            data=make_job(im,*self.settings(),invert=self.invert.get()) if kind=='prn' else None
            path=filedialog.asksaveasfilename(defaultextension='.'+kind,filetypes=[(kind.upper(),'*.'+kind)])
            if path:
                if data is None: im.save(path)
                else: Path(path).write_bytes(data)
                self.status.config(text='Saved '+path)
        except Exception as exc:messagebox.showerror('Export failed',str(exc))

    def print_label(self):
        if self.busy:return
        try:
            im=self.render(); settings=self.settings()
            payload=make_job(im,*settings,invert=self.invert.get())
            name=self.vars['printer'].get().strip()
            if name not in self.usb_paths:raise ValueError('Connect the printer and refresh first.')
            path=self.usb_paths[name]
            if not self.preview():return
            if not messagebox.askyesno('Print label',f'Send {settings[3]} label(s) to {name}?\n\nStock: {settings[0]:g} x {settings[1]:g} mm; gap {settings[2]:g} mm.\nCheck the loaded stock before printing.'):
                return
            self.busy=True; self.print_button.state(['disabled'])
            self.status.config(text='Sending directly to USB...')
            def work():
                try:
                    count=send_raw(path,payload)
                    result=f'Sent {count:,} bytes directly to USB. Check the physical label.'
                except Exception as exc:result='Print failed: '+str(exc)
                def finish():
                    self.busy=False; self.print_button.state(['!disabled']); self.status.config(text=result)
                self.root.after(0,finish)
            threading.Thread(target=work,daemon=True).start()
        except Exception as exc:messagebox.showerror('Could not print',str(exc))

if __name__=='__main__':
    root=tk.Tk(); app=App(root)
    if '--smoke-test' in sys.argv:
        def smoke():
            try:
                assert app.preview()
                im=app.render(); job=make_job(im,*app.settings())
                assert job.endswith(b'PRINT 1,1\r\n')
                root.destroy()
            except Exception:
                root.destroy(); raise SystemExit(1)
        root.after(500,smoke)
    root.mainloop()
