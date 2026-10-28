import base64, io, json, os, shutil, subprocess, tempfile, zipfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

APP = "Picture Animator"
FFMPEG = Path.home() / "ffmpeg.exe"
SHAPES = ("Box", "Right arrow", "Left arrow", "Up arrow", "Down arrow")

class Animator(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP); self.geometry("1280x800"); self.minsize(950,650)
        self.frames=[]; self.current=-1; self.selected=None; self.project_path=None; self.tkimg=None; self.scale=1; self.drag=None
        self._ui(); self.bind("<Control-s>", lambda e:self.save())
    def _ui(self):
        top=ttk.Frame(self,padding=8); top.pack(fill="x")
        for text,cmd in [("New",self.new),("Add pictures",self.add_pictures),("Open project",self.open_project),("Save",self.save),("Save as",self.save_as),("Export MP4",self.export_mp4)]: ttk.Button(top,text=text,command=cmd).pack(side="left",padx=3)
        ttk.Label(top,text="  Projects are saved as .paanim files, including their pictures.").pack(side="left")
        body=ttk.PanedWindow(self,orient="horizontal"); body.pack(fill="both",expand=True,padx=8,pady=(0,8))
        left=ttk.Frame(body,padding=8); body.add(left,weight=1)
        ttk.Label(left,text="Frames (double-click name to rename)",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.listbox=tk.Listbox(left); self.listbox.pack(fill="both",expand=True); self.listbox.bind("<<ListboxSelect>>",self.pick_frame); self.listbox.bind("<Double-Button-1>",self.rename_frame)
        r=ttk.Frame(left);r.pack(fill="x",pady=6)
        for t,c in [("↑",lambda:self.move(-1)),("↓",lambda:self.move(1)),("Delete",self.delete_frame)]:ttk.Button(r,text=t,command=c).pack(side="left",padx=2)
        ttk.Label(left,text="Frames per second").pack(anchor="w"); self.fps=tk.DoubleVar(value=1); ttk.Spinbox(left,from_=0.1,to=30,increment=.1,textvariable=self.fps,width=8).pack(anchor="w")
        middle=ttk.Frame(body,padding=8);body.add(middle,weight=4)
        ttk.Label(middle,text="Preview — drag labels to position them",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.canvas=tk.Canvas(middle,bg="#e9edf3",highlightthickness=0);self.canvas.pack(fill="both",expand=True,pady=(5,0));self.canvas.bind("<Configure>",lambda e:self.draw());self.canvas.bind("<ButtonPress-1>",self.down);self.canvas.bind("<B1-Motion>",self.motion);self.canvas.bind("<ButtonRelease-1>",self.up)
        right=ttk.Frame(body,padding=8);body.add(right,weight=1)
        ttk.Button(right,text="+ Add label",command=self.add_label).pack(fill="x")
        ttk.Button(right,text="Delete label",command=self.delete_label).pack(fill="x",pady=4)
        self.fields={}
        for key,title in [("text","Text"),("shape","Shape"),("size","Text size"),("color","Text color (#RRGGBB)"),("bg","Background (#RRGGBB)"),("delay","Appear after (seconds)")]:
            ttk.Label(right,text=title).pack(anchor="w",pady=(7,0))
            if key=="shape": w=ttk.Combobox(right,values=SHAPES,state="readonly")
            else:w=ttk.Entry(right)
            w.pack(fill="x");w.bind("<KeyRelease>",lambda e:self.apply_fields());w.bind("<<ComboboxSelected>>",lambda e:self.apply_fields());self.fields[key]=w
        self.status=tk.StringVar(value="Add pictures to begin.");ttk.Label(self,textvariable=self.status,anchor="w",padding=6).pack(fill="x")
    def new(self): self.frames=[];self.current=-1;self.selected=None;self.project_path=None;self.refresh()
    def add_pictures(self):
        files=filedialog.askopenfilenames(filetypes=[("Pictures","*.png *.jpg *.jpeg *.webp *.bmp")])
        for f in files:
            data=Path(f).read_bytes(); self.frames.append({"name":Path(f).stem,"image":base64.b64encode(data).decode(),"labels":[]})
        if files:self.current=len(self.frames)-len(files);self.refresh();self.status.set(f"Added {len(files)} picture(s). Save project to keep them.")
    def frame_image(self,f): return Image.open(io.BytesIO(base64.b64decode(f["image"]))).convert("RGB")
    def refresh(self):
        self.listbox.delete(0,"end")
        for i,f in enumerate(self.frames):self.listbox.insert("end",f"{i+1}. {f['name']}")
        if self.current>=0 and self.frames:self.listbox.selection_set(self.current)
        self.draw();self.load_fields()
    def pick_frame(self,e=None):
        x=self.listbox.curselection()
        if x:self.current=x[0];self.selected=None;self.draw();self.load_fields()
    def rename_frame(self,e=None):
        if self.current<0:return
        box=tk.Toplevel(self);box.title("Rename frame");v=tk.StringVar(value=self.frames[self.current]['name']);ttk.Entry(box,textvariable=v,width=35).pack(padx=10,pady=10);ttk.Button(box,text="Save",command=lambda:(self.frames[self.current].update(name=v.get().strip() or 'Untitled frame'),box.destroy(),self.refresh())).pack(pady=(0,10))
    def move(self,d):
        n=self.current+d
        if 0<=n<len(self.frames):self.frames[self.current],self.frames[n]=self.frames[n],self.frames[self.current];self.current=n;self.refresh()
    def delete_frame(self):
        if self.current>=0:self.frames.pop(self.current);self.current=min(self.current,len(self.frames)-1);self.selected=None;self.refresh()
    def label(self):
        if self.current<0:return None
        return next((x for x in self.frames[self.current]['labels'] if x['id']==self.selected),None)
    def add_label(self):
        if self.current<0:return
        l={"id":os.urandom(6).hex(),"text":"Your label","shape":"Box","x":.5,"y":.5,"size":28,"color":"#FFFFFF","bg":"#5B46C8","delay":0};self.frames[self.current]['labels'].append(l);self.selected=l['id'];self.draw();self.load_fields()
    def delete_label(self):
        if self.current<0 or not self.selected:return
        self.frames[self.current]['labels']=[x for x in self.frames[self.current]['labels'] if x['id']!=self.selected];self.selected=None;self.draw();self.load_fields()
    def load_fields(self):
        l=self.label()
        for key,w in self.fields.items():w.delete(0,"end");w.insert(0,str(l[key]) if l else "")
    def apply_fields(self):
        l=self.label()
        if not l:return
        try:l['text']=self.fields['text'].get();l['shape']=self.fields['shape'].get() or 'Box';l['size']=max(8,int(self.fields['size'].get()));l['color']=self.fields['color'].get() or '#FFFFFF';l['bg']=self.fields['bg'].get() or '#5B46C8';l['delay']=max(0,float(self.fields['delay'].get() or 0));self.draw()
        except ValueError:pass
    def draw(self):
        self.canvas.delete("all")
        if self.current<0 or self.current>=len(self.frames):return
        im=self.frame_image(self.frames[self.current]);cw,ch=self.canvas.winfo_width(),self.canvas.winfo_height();self.scale=min(max(1,cw)/im.width,max(1,ch)/im.height);w,h=int(im.width*self.scale),int(im.height*self.scale);x,y=(cw-w)//2,(ch-h)//2;self.origin=(x,y,w,h);self.tkimg=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS));self.canvas.create_image(x,y,anchor="nw",image=self.tkimg)
        for l in self.frames[self.current]['labels']:
            px=x+l['x']*w;py=y+l['y']*h;fs=max(10,int(l['size']*self.scale));font=("Segoe UI",fs,"bold");wid=max(50,self.canvas.create_text(px,py,text=l['text'],font=font,state="hidden"));bbox=self.canvas.bbox(wid);self.canvas.delete(wid);tw=max(65,bbox[2]-bbox[0]+22);th=max(28,bbox[3]-bbox[1]+14);pts=self.shape(l['shape'],px,py,tw,th);self.canvas.create_polygon(pts,fill=l['bg'],outline="#111" if l['id']==self.selected else "");self.canvas.create_text(px,py,text=l['text'],fill=l['color'],font=font,tags=("label",l['id']))
    def shape(self,s,x,y,w,h):
        a=w/2;b=h/2
        if s=='Right arrow':return [x-a,y-b,x+a-18,y-b,x+a,y,x+a-18,y+b,x-a,y+b]
        if s=='Left arrow':return [x-a+18,y-b,x+a,y-b,x+a,y+b,x-a+18,y+b,x-a,y]
        if s=='Up arrow':return [x,y-b,x+a,y-b+18,x+a,y+b,x-a,y+b,x-a,y-b+18]
        if s=='Down arrow':return [x-a,y-b,x+a,y-b,x+a,y+b-18,x,y+b,x-a,y+b-18]
        return [x-a,y-b,x+a,y-b,x+a,y+b,x-a,y+b]
    def down(self,e):
        if self.current<0:return
        ids=self.canvas.find_overlapping(e.x,e.y,e.x,e.y)
        for i in reversed(ids):
            tags=self.canvas.gettags(i)
            if len(tags)>1 and tags[0]=='label':self.selected=tags[1];self.drag=(e.x,e.y);self.draw();self.load_fields();return
        self.selected=None;self.draw();self.load_fields()
    def motion(self,e):
        l=self.label()
        if not l or not self.drag:return
        x,y,w,h=self.origin;l['x']=max(0,min(1,(e.x-x)/w));l['y']=max(0,min(1,(e.y-y)/h));self.draw()
    def up(self,e):self.drag=None
    def save_data(self,path):
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('project.json',json.dumps({"version":1,"frames":self.frames}))
    def save(self):
        if not self.frames:return
        if not self.project_path:return self.save_as()
        self.save_data(self.project_path);self.status.set(f"Saved: {self.project_path.name}")
    def save_as(self):
        if not self.frames:return
        name=filedialog.asksaveasfilename(defaultextension='.paanim',filetypes=[("Picture Animator project","*.paanim")])
        if name:self.project_path=Path(name);self.save()
    def open_project(self):
        name=filedialog.askopenfilename(filetypes=[("Picture Animator project","*.paanim")])
        if not name:return
        try:
            with zipfile.ZipFile(name) as z:self.frames=json.loads(z.read('project.json'))['frames']
            self.project_path=Path(name);self.current=0 if self.frames else -1;self.selected=None;self.refresh();self.status.set(f"Opened: {self.project_path.name}")
        except Exception as e:messagebox.showerror(APP,f"Could not open project:\n{e}")
    def export_mp4(self):
        if not self.frames:return
        target=filedialog.asksaveasfilename(defaultextension='.mp4',filetypes=[("MP4 video","*.mp4")])
        if not target:return
        ff=FFMPEG if FFMPEG.exists() else shutil.which('ffmpeg')
        if not ff:return messagebox.showerror(APP,'FFmpeg was not found.')
        try:
            with tempfile.TemporaryDirectory() as d:
                for n,f in enumerate(self.frames):
                    im=self.frame_image(f);draw=ImageDraw.Draw(im);font_path='C:/Windows/Fonts/arialbd.ttf'
                    for l in f['labels']:
                        font=ImageFont.truetype(font_path,l['size']);x,y=int(l['x']*im.width),int(l['y']*im.height);box=draw.textbbox((x,y),l['text'],font=font,anchor='mm');pad=12;draw.rectangle((box[0]-pad,box[1]-pad,box[2]+pad,box[3]+pad),fill=l['bg']);draw.text((x,y),l['text'],font=font,fill=l['color'],anchor='mm')
                    im.save(Path(d)/f'{n:05d}.png')
                rate=max(.1,float(self.fps.get()));subprocess.run([str(ff),'-y','-framerate',str(rate),'-i',str(Path(d)/'%05d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',target],check=True,capture_output=True)
            self.status.set(f"MP4 exported: {Path(target).name}")
        except Exception as e:messagebox.showerror(APP,f"MP4 export failed:\n{e}")
if __name__=='__main__':Animator().mainloop()
