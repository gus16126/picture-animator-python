import base64, io, json, os, shutil, subprocess, tempfile, zipfile
from pathlib import Path
import re
import math
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps, ImageColor, UnidentifiedImageError

APP = "Picture Animator"
FFMPEG = Path.home() / "ffmpeg.exe"
SHAPES = ("Box", "Right arrow", "Left arrow", "Up arrow", "Down arrow")
TRANSITIONS = ("Cut", "Fade", "Slide left", "Slide right", "Zoom")
ANIMATIONS = ("None", "Fade in", "Fade out", "Slide left", "Slide right", "Pop", "Typewriter")
LABEL_PAD = 24
ARROW_TIP = 48
FONTS = ("Arial Bold", "Segoe UI Bold", "Calibri Bold")
PRESETS_FILE = Path(__file__).with_name("label_presets.json")
STYLE_KEYS = ("shape", "font", "size", "color", "bg", "outline", "opacity", "rotation")

class Animator(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP); self.geometry("1280x800"); self.minsize(950,650)
        self.frames=[]; self.current=-1; self.selected=None; self.project_path=None; self.audio_path=None; self.tkimg=None; self.scale=1; self.drag=None; self._img_cache={}
        self.presets=self.load_presets()
        self.playing=False;self.play_started=0;self.play_origin=0;self.timeline_active=False
        self._ui(); self.bind("<Control-s>", lambda e:self.save())
    def _ui(self):
        top=ttk.Frame(self,padding=8); top.pack(fill="x")
        for text,cmd in [("New",self.new),("Add pictures",self.add_pictures),("Open project",self.open_project),("Save",self.save),("Save as",self.save_as),("Export MP4",self.export_mp4)]: ttk.Button(top,text=text,command=cmd).pack(side="left",padx=3)
        ttk.Button(top,text="Add audio",command=self.add_audio).pack(side="left",padx=3)
        ttk.Label(top,text="  Projects are saved as .paanim files, including their pictures.").pack(side="left")
        body=ttk.PanedWindow(self,orient="horizontal"); body.pack(fill="both",expand=True,padx=8,pady=(0,8))
        left=ttk.Frame(body,padding=8); body.add(left,weight=1)
        ttk.Label(left,text="Frames (double-click name to rename)",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.listbox=tk.Listbox(left,selectmode='extended'); self.listbox.pack(fill="both",expand=True); self.listbox.bind("<<ListboxSelect>>",self.pick_frame); self.listbox.bind("<Double-Button-1>",self.rename_frame);self.listbox.bind("<ButtonPress-1>",self.frame_drag_start,add='+');self.listbox.bind("<B1-Motion>",self.frame_drag_move)
        r=ttk.Frame(left);r.pack(fill="x",pady=6)
        for t,c in [("↑",lambda:self.move(-1)),("↓",lambda:self.move(1)),("Duplicate",self.duplicate_frame),("Delete",self.delete_frame)]:ttk.Button(r,text=t,command=c).pack(side="left",padx=2)
        ttk.Label(left,text="Frame duration (seconds)").pack(anchor="w");self.duration=tk.StringVar(value="1.0");self.duration_input=ttk.Spinbox(left,from_=0.1,to=3600,increment=.1,textvariable=self.duration,width=8,command=self.apply_duration);self.duration_input.pack(anchor="w");self.duration_input.bind("<KeyRelease>",lambda e:self.apply_duration());self.duration_input.bind("<FocusOut>",lambda e:self.apply_duration())
        ttk.Label(left,text="Transition into this frame").pack(anchor="w",pady=(7,0));self.transition=tk.StringVar(value="Cut");self.transition_input=ttk.Combobox(left,values=TRANSITIONS,textvariable=self.transition,state="readonly",width=13);self.transition_input.pack(anchor="w");self.transition_input.bind("<<ComboboxSelected>>",lambda e:self.apply_transition())
        ttk.Label(left,text="Transition duration (seconds)").pack(anchor="w");self.transition_duration_value=tk.StringVar(value="0.3");self.transition_duration_input=ttk.Spinbox(left,from_=0.1,to=10,increment=.1,textvariable=self.transition_duration_value,width=8,command=self.apply_transition);self.transition_duration_input.pack(anchor="w");self.transition_duration_input.bind("<KeyRelease>",lambda e:self.apply_transition());self.transition_duration_input.bind("<FocusOut>",lambda e:self.apply_transition())
        ttk.Button(left,text="Apply timing to selected",command=self.apply_timing_to_selected).pack(anchor="w",pady=(5,0))
        ttk.Label(left,text="Export FPS").pack(anchor="w",pady=(7,0)); self.fps=tk.DoubleVar(value=10); ttk.Spinbox(left,from_=1,to=30,increment=1,textvariable=self.fps,width=8).pack(anchor="w")
        middle=ttk.Frame(body,padding=8);body.add(middle,weight=6)
        ttk.Label(middle,text="Preview — drag labels; right-click to add/delete",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.canvas=tk.Canvas(middle,bg="#e9edf3",highlightthickness=0);self.canvas.pack(fill="both",expand=True,pady=(5,0));self.canvas.bind("<Configure>",lambda e:self.render_timeline() if self.timeline_active else self.draw());self.canvas.bind("<ButtonPress-1>",self.down);self.canvas.bind("<B1-Motion>",self.motion);self.canvas.bind("<ButtonRelease-1>",self.up);self.canvas.bind("<Button-3>",self.canvas_menu)
        transport=ttk.Frame(middle);transport.pack(fill="x",pady=(6,0));self.play_button=ttk.Button(transport,text="▶ Play",command=self.toggle_play);self.play_button.pack(side="left");self.timeline=tk.DoubleVar(value=0);self.timeline_scale=ttk.Scale(transport,from_=0,to=1,variable=self.timeline,command=self.seek_timeline);self.timeline_scale.pack(side="left",fill="x",expand=True,padx=8);self.timeline_text=tk.StringVar(value="0:00.0 / 0:00.0");ttk.Label(transport,textvariable=self.timeline_text,width=15).pack(side="right")
        right=ttk.Frame(body,padding=8);body.add(right,weight=1)
        ttk.Button(right,text="+ Add label",command=self.add_label).pack(fill="x")
        ttk.Button(right,text="Delete label",command=self.delete_label).pack(fill="x",pady=4)
        self.preset_choice=tk.StringVar();self.preset_input=ttk.Combobox(right,values=sorted(self.presets),textvariable=self.preset_choice,state="readonly");self.preset_input.pack(fill="x",pady=(8,0));ttk.Button(right,text="Save preset",command=self.save_preset).pack(fill="x",pady=(4,0));ttk.Button(right,text="Apply preset",command=self.apply_preset_to_matching).pack(fill="x",pady=4)
        self.fields={}
        for key,title in [("text","Text"),("shape","Shape"),("font","Font"),("size","Text size"),("color","Text color"),("bg","Background"),("outline","Outline"),("opacity","Opacity"),("rotation","Rotation"),("delay","Appear after (s)"),("animation","Animation"),("anim_duration","Animation time (s)")]:
            ttk.Label(right,text=title).pack(anchor="w",pady=(7,0))
            if key=="shape": w=ttk.Combobox(right,values=SHAPES,state="readonly")
            elif key=="font": w=ttk.Combobox(right,values=FONTS,state="readonly")
            elif key=="animation": w=ttk.Combobox(right,values=ANIMATIONS,state="readonly")
            elif key=="text": w=tk.Text(right,height=3,wrap="word",width=18)
            else:w=ttk.Entry(right)
            w.pack(fill="x");w.bind("<KeyRelease>",lambda e:self.apply_fields());w.bind("<<ComboboxSelected>>",lambda e:self.apply_fields());self.fields[key]=w
        self.status=tk.StringVar(value="Add pictures to begin.");ttk.Label(self,textvariable=self.status,anchor="w",padding=6).pack(fill="x")
    def new(self): self.stop_playback();self.frames=[];self.current=-1;self.selected=None;self.project_path=None;self.audio_path=None;self._img_cache={};self.refresh()
    def add_audio(self):
        name=filedialog.askopenfilename(filetypes=[("Audio","*.mp3 *.wav *.m4a *.aac *.ogg *.flac")])
        if name:self.audio_path=Path(name);self.status.set(f"Audio: {self.audio_path.name}")
    def add_pictures(self):
        files=filedialog.askopenfilenames(filetypes=[("Pictures","*.png *.jpg *.jpeg *.webp *.bmp")])
        rejected=[];first_new=len(self.frames)
        for f in files:
            try:
                data=Path(f).read_bytes()
                with Image.open(io.BytesIO(data)) as image: image.verify()
                self.frames.append({"name":Path(f).stem,"image":base64.b64encode(data).decode(),"labels":[],"duration":1.0,"transition":"Cut","transition_duration":.3})
            except (OSError, UnidentifiedImageError):
                rejected.append(Path(f).name)
        if len(self.frames)>first_new:
            self.current=first_new;self.refresh()
            self.status.set(f"Added {len(files)-len(rejected)} picture(s). Save project to keep them.")
        if rejected:
            messagebox.showwarning(APP, "Some pictures were skipped", "Could not read:\n" + "\n".join(rejected))
    def frame_image(self,f):
        key=f["image"]; im=self._img_cache.get(key)
        if im is None:
            with Image.open(io.BytesIO(base64.b64decode(key))) as image:
                im=ImageOps.exif_transpose(image).convert("RGB")
            self._img_cache[key]=im
        return im.copy()
    def frame_duration(self, frame):
        try:return max(.1,float(frame.get('duration',1.0)))
        except (TypeError,ValueError):return 1.0
    def total_duration(self): return sum(self.frame_duration(frame) for frame in self.frames)
    def format_time(self, seconds):
        minutes,seconds=divmod(max(0,seconds),60)
        return f"{int(minutes)}:{seconds:04.1f}"
    def update_timeline(self):
        total=self.total_duration();self.timeline_scale.configure(to=max(.1,total))
        self.timeline.set(min(self.timeline.get(),total));self.timeline_text.set(f"{self.format_time(self.timeline.get())} / {self.format_time(total)}")
    def frame_at_time(self, position):
        elapsed=0
        for index,frame in enumerate(self.frames):
            duration=self.frame_duration(frame)
            if position<elapsed+duration or index==len(self.frames)-1:return index,max(0,min(duration,position-elapsed))
            elapsed+=duration
        return -1,0
    def load_duration(self):
        value=self.frame_duration(self.frames[self.current]) if 0<=self.current<len(self.frames) else 1.0
        self.duration.set(f"{value:g}")
    def apply_duration(self):
        if self.current<0:return
        try:value=max(.1,float(self.duration.get()))
        except ValueError:return
        self.frames[self.current]['duration']=value;self.update_timeline()
    def transition_for(self, frame):
        value=frame.get('transition','Cut')
        return value if value in TRANSITIONS else 'Cut'
    def transition_duration_for(self, frame):
        try:return max(.1,float(frame.get('transition_duration',.3)))
        except (TypeError,ValueError):return .3
    def load_transition(self):
        frame=self.frames[self.current] if 0<=self.current<len(self.frames) else {}
        self.transition.set(self.transition_for(frame));self.transition_duration_value.set(f"{self.transition_duration_for(frame):g}")
    def apply_transition(self):
        if self.current<0:return
        try:duration=max(.1,float(self.transition_duration_value.get()))
        except ValueError:return
        self.frames[self.current]['transition']=self.transition.get() if self.transition.get() in TRANSITIONS else 'Cut'
        self.frames[self.current]['transition_duration']=duration
        if self.timeline_active:self.render_timeline()
    def selected_frames(self): return [self.frames[i] for i in self.listbox.curselection() if 0<=i<len(self.frames)]
    def apply_timing_to_selected(self):
        frames=self.selected_frames()
        if not frames:return
        try:duration=max(.1,float(self.duration.get()));transition_duration=max(.1,float(self.transition_duration_value.get()))
        except ValueError:return
        for frame in frames:frame['duration']=duration;frame['transition']=self.transition.get();frame['transition_duration']=transition_duration
        self.update_timeline();self.status.set(f'Applied timing to {len(frames)} frame(s).')
    def refresh(self):
        self.listbox.delete(0,"end")
        for i,f in enumerate(self.frames):
            self.listbox.insert("end",f"{i+1}. {f['name']}")
        if self.current>=0 and self.frames:self.listbox.selection_set(self.current)
        self.timeline_active=False;self.update_timeline();self.draw();self.load_fields();self.load_duration();self.load_transition()
    def pick_frame(self,e=None):
        x=self.listbox.curselection()
        if x:
            self.stop_playback();self.current=x[0];self.selected=None;self.timeline_active=False;self.draw();self.load_fields();self.load_duration();self.load_transition()
    def rename_frame(self,e=None):
        if self.current<0:return
        box=tk.Toplevel(self);box.title("Rename frame");v=tk.StringVar(value=self.frames[self.current]['name']);ttk.Entry(box,textvariable=v,width=35).pack(padx=10,pady=10);ttk.Button(box,text="Save",command=lambda:(self.frames[self.current].update(name=v.get().strip() or 'Untitled frame'),box.destroy(),self.refresh())).pack(pady=(0,10))
    def move(self,d):
        n=self.current+d
        if 0<=n<len(self.frames):self.frames[self.current],self.frames[n]=self.frames[n],self.frames[self.current];self.current=n;self.refresh()
    def frame_drag_start(self,event): self.frame_drag_index=self.listbox.nearest(event.y)
    def frame_drag_move(self,event):
        target=self.listbox.nearest(event.y);source=getattr(self,'frame_drag_index',-1)
        if source<0 or target==source or not (0<=target<len(self.frames)):return
        frame=self.frames.pop(source);self.frames.insert(target,frame);self.current=target;self.frame_drag_index=target;self.refresh();self.status.set('Reordered frame.')
    def delete_frame(self):
        if self.current>=0:self.stop_playback();self.frames.pop(self.current);self.current=min(self.current,len(self.frames)-1);self.selected=None;self.refresh()
    def duplicate_frame(self):
        if self.current<0:return
        duplicate=json.loads(json.dumps(self.frames[self.current]));duplicate['name']=f"{duplicate.get('name','Frame')} copy"
        self.frames.insert(self.current+1,duplicate);self.current+=1;self.selected=None;self.refresh();self.status.set('Duplicated frame.')
    def label(self):
        if self.current<0:return None
        return next((x for x in self.frames[self.current]['labels'] if x['id']==self.selected),None)
    def load_presets(self):
        try:
            data=json.loads(PRESETS_FILE.read_text(encoding='utf-8'))
            return data if isinstance(data,dict) else {}
        except (OSError,ValueError):return {}
    def persist_presets(self):
        PRESETS_FILE.write_text(json.dumps(self.presets,indent=2),encoding='utf-8')
        self.preset_input.configure(values=sorted(self.presets))
    def save_preset(self):
        label=self.label()
        if not label:return
        box=tk.Toplevel(self);box.title('Save label style preset');name=tk.StringVar();ttk.Label(box,text='Preset name').pack(padx=12,pady=(12,0));entry=ttk.Entry(box,textvariable=name,width=32);entry.pack(padx=12,pady=6);entry.focus_set()
        def save():
            key=name.get().strip()
            if not key:return
            self.presets[key]={style:label.get(style) for style in STYLE_KEYS};self.persist_presets();self.preset_choice.set(key);box.destroy()
        ttk.Button(box,text='Save preset',command=save).pack(pady=(0,12))
    def apply_preset_to_matching(self):
        label=self.label();preset=self.presets.get(self.preset_choice.get())
        if not label or not preset:return
        changed=0
        for frame in self.frames:
            for candidate in frame.get('labels',[]):
                if candidate.get('text')==label.get('text'):
                    candidate.update(preset);changed+=1
        self.draw();self.load_fields();self.status.set(f"Applied preset to {changed} label(s) named {label.get('text')!r}.")
    def add_label(self):
        if self.current<0:return
        l={"id":os.urandom(6).hex(),"text":"Your label","shape":"Box","font":"Arial Bold","x":.5,"y":.5,"size":28,"color":"#FFFFFF","bg":"#5B46C8","outline":"","opacity":100,"rotation":0,"animation":"None","anim_duration":.5,"delay":0};self.frames[self.current]['labels'].append(l);self.selected=l['id'];self.draw();self.load_fields()
    def delete_label(self):
        if self.current<0 or not self.selected:return
        self.frames[self.current]['labels']=[x for x in self.frames[self.current]['labels'] if x['id']!=self.selected];self.selected=None;self.draw();self.load_fields()
    def load_fields(self):
        l=self.label()
        for key,w in self.fields.items():
            if key=="text":w.delete("1.0","end");w.insert("1.0",str(l[key]) if l else "")
            else:w.delete(0,"end");w.insert(0,str(l[key]) if l else "")
    def valid_color(self, value): return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", value))
    def apply_fields(self):
        l=self.label()
        if not l:return
        l['text']=self.fields['text'].get("1.0","end-1c");l['shape']=self.fields['shape'].get() or 'Box';l['font']=self.fields['font'].get() or 'Arial Bold'
        try:l['size']=max(8,int(self.fields['size'].get()))
        except ValueError:pass
        color=self.fields['color'].get();bg=self.fields['bg'].get()
        if self.valid_color(color):l['color']=color
        if self.valid_color(bg):l['bg']=bg
        outline=self.fields['outline'].get()
        if not outline or self.valid_color(outline):l['outline']=outline
        try:l['opacity']=max(0,min(100,int(self.fields['opacity'].get())))
        except ValueError:pass
        try:l['rotation']=float(self.fields['rotation'].get())
        except ValueError:pass
        try:l['delay']=max(0,float(self.fields['delay'].get() or 0))
        except ValueError:pass
        anim=self.fields['animation'].get()
        if anim in ANIMATIONS:l['animation']=anim
        try:l['anim_duration']=max(.1,float(self.fields['anim_duration'].get() or .5))
        except ValueError:pass
        self.draw()
    def render_timeline(self):
        if not self.frames:return
        total=self.total_duration();position=min(max(0,self.timeline.get()),total);self.timeline.set(position)
        index,local_time=self.frame_at_time(position)
        if index!=self.current:
            self.current=index;self.selected=None;self.listbox.selection_clear(0,'end');self.listbox.selection_set(index);self.listbox.activate(index);self.load_fields();self.load_duration();self.load_transition()
        self.timeline_text.set(f"{self.format_time(position)} / {self.format_time(total)}")
        self.draw(local_time)
    def seek_timeline(self, value):
        if self.playing:self.stop_playback()
        self.timeline_active=True;self.timeline.set(float(value));self.render_timeline()
    def toggle_play(self):
        if not self.frames:return
        if self.playing:self.stop_playback();return
        total=self.total_duration();origin=min(self.timeline.get(),total)
        if origin>=total:origin=0;self.timeline.set(0)
        self.playing=True;self.timeline_active=True;self.play_origin=origin;self.play_started=time.perf_counter();self.play_button.configure(text="❚❚ Pause");self.play_tick()
    def stop_playback(self):
        self.playing=False
        if hasattr(self,'play_button'):self.play_button.configure(text="▶ Play")
    def play_tick(self):
        if not self.playing:return
        position=self.play_origin+(time.perf_counter()-self.play_started);total=self.total_duration()
        if position>=total:
            self.timeline.set(total);self.render_timeline();self.stop_playback();return
        self.timeline.set(position);self.render_timeline();self.after(30,self.play_tick)
    def render_frame_image(self, frame, local_time=None):
        image=self.frame_image(frame);duration=self.frame_duration(frame)
        for label in frame['labels']:
            delay=label.get('delay',0);anim=label.get('animation','None');adur=max(.1,float(label.get('anim_duration',.5)))
            if local_time is None:
                self.draw_export_label(image,label,1.0,1.0);continue
            if anim=='Fade out':
                if local_time<delay:continue
                fade_start=max(delay,duration-adur)
                alpha=1.0 if local_time<fade_start else max(0.0,1.0-(local_time-fade_start)/adur)
                if alpha<=0:continue
                self.draw_export_label(image,label,1.0,alpha)
            else:
                if local_time<delay:continue
                p=1.0 if anim=='None' or local_time>=delay+adur else (local_time-delay)/adur
                p=max(0.0,min(1.0,p));a=p if anim=='Fade in' else 1.0
                self.draw_export_label(image,label,p,a)
        return image
    def center_on_canvas(self, image, width, height):
        canvas=Image.new('RGB',(width,height),'black');canvas.paste(image,((width-image.width)//2,(height-image.height)//2));return canvas
    def transition_image(self, index, local_time):
        frame=self.frames[index];current=self.render_frame_image(frame,local_time)
        style=self.transition_for(frame);duration=self.transition_duration_for(frame)
        if index==0 or local_time is None or style=='Cut' or local_time>=duration:return current
        previous=self.render_frame_image(self.frames[index-1],self.frame_duration(self.frames[index-1]))
        width=max(previous.width,current.width);height=max(previous.height,current.height);previous=self.center_on_canvas(previous,width,height);current=self.center_on_canvas(current,width,height);progress=max(0,min(1,local_time/duration))
        if style=='Fade':return Image.blend(previous,current,progress)
        if style.startswith('Slide'):
            result=Image.new('RGB',(width,height),'black');shift=int(width*progress)
            if style=='Slide left':result.paste(previous,(-shift,0));result.paste(current,(width-shift,0))
            else:result.paste(previous,(shift,0));result.paste(current,(-width+shift,0))
            return result
        if style=='Zoom':
            scale=.2+.8*progress;size=(max(1,int(width*scale)),max(1,int(height*scale)));zoomed=current.resize(size,Image.Resampling.LANCZOS);result=previous.copy();overlay=Image.new('RGB',(width,height),'black');overlay.paste(zoomed,((width-size[0])//2,(height-size[1])//2));return Image.blend(result,overlay,progress)
        return current
    def draw(self, local_time=None):
        self.canvas.delete("all")
        if self.current<0 or self.current>=len(self.frames):return
        try:im=self.transition_image(self.current,local_time)
        except (OSError, ValueError, UnidentifiedImageError) as e:self.status.set(f"Could not display this picture: {e}");return
        cw,ch=self.canvas.winfo_width(),self.canvas.winfo_height();self.scale=min(max(1,cw)/im.width,max(1,ch)/im.height);w,h=int(im.width*self.scale),int(im.height*self.scale);x,y=(cw-w)//2,(ch-h)//2;self.origin=(x,y,w,h);self.tkimg=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS));self.canvas.create_image(x,y,anchor="nw",image=self.tkimg)
    def shape(self,s,x,y,w,h):
        a=w/2;b=h/2;tip=min(ARROW_TIP,max(12,min(w*.4,h*.9)))
        if s=='Right arrow':return [x-a,y-b,x+a-tip,y-b,x+a,y,x+a-tip,y+b,x-a,y+b]
        if s=='Left arrow':return [x-a+tip,y-b,x+a,y-b,x+a,y+b,x-a+tip,y+b,x-a,y]
        if s=='Up arrow':return [x,y-b,x+a,y-b+tip,x+a,y+b,x-a,y+b,x-a,y-b+tip]
        if s=='Down arrow':return [x-a,y-b,x+a,y-b,x+a,y+b-tip,x,y+b,x-a,y+b-tip]
        return [x-a,y-b,x+a,y-b,x+a,y+b,x-a,y+b]
    def down(self,e):
        if self.current<0:return
        self.stop_playback();self.timeline_active=False
        self.draw();x,y,w,h=self.origin
        for label in reversed(self.frames[self.current]['labels']):
            tw,th=self._label_box(label);tw*=self.scale;th*=self.scale;px=x+label['x']*w;py=y+label['y']*h
            if px-tw/2<=e.x<=px+tw/2 and py-th/2<=e.y<=py+th/2:self.selected=label['id'];self.drag=(e.x,e.y);self.draw();self.load_fields();return
        self.selected=None;self.draw();self.load_fields()
    def motion(self,e):
        l=self.label()
        if not l or not self.drag:return
        x,y,w,h=self.origin;l['x']=max(0,min(1,(e.x-x)/w));l['y']=max(0,min(1,(e.y-y)/h));self.draw()
    def up(self,e):self.drag=None
    def canvas_menu(self,event):
        if self.current<0:return
        self.down(event);self.drag=None
        menu=tk.Menu(self,tearoff=0)
        menu.add_command(label="Add label",command=self.add_label)
        menu.add_command(label="Delete label",command=self.delete_label,state="normal" if self.selected else "disabled")
        try:menu.tk_popup(event.x_root,event.y_root)
        finally:menu.grab_release()
    def save_data(self,path):
        temp=Path(str(path)+'.tmp')
        try:
            with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('project.json',json.dumps({"version":1,"frames":self.frames,"audio_path":str(self.audio_path) if self.audio_path else None}))
            temp.replace(path)
        finally:
            if temp.exists():temp.unlink()
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
            with zipfile.ZipFile(name) as z:data=json.loads(z.read('project.json'));self.frames=data['frames'];self.audio_path=Path(data['audio_path']) if data.get('audio_path') else None
            for frame in self.frames:
                frame.setdefault('duration',1.0);frame.setdefault('transition','Cut');frame.setdefault('transition_duration',.3)
                for label in frame.get('labels',[]):
                    label.setdefault('font','Arial Bold');label.setdefault('outline','');label.setdefault('opacity',100);label.setdefault('rotation',0);label.setdefault('animation','None');label.setdefault('anim_duration',.5)
            self.project_path=Path(name);self.current=0 if self.frames else -1;self.selected=None;self._img_cache={};self.refresh();self.status.set(f"Opened: {self.project_path.name}")
        except Exception as e:messagebox.showerror(APP,f"Could not open project:\n{e}")
    def font_for_export(self, size, family='Arial Bold'):
        paths={'Arial Bold':'C:/Windows/Fonts/arialbd.ttf','Segoe UI Bold':'C:/Windows/Fonts/segoeuib.ttf','Calibri Bold':'C:/Windows/Fonts/calibrib.ttf'}
        for path in (paths.get(family), 'C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/segoeuib.ttf'):
            if Path(path).exists():return ImageFont.truetype(path,size)
        return ImageFont.load_default()
    def _line_spacing(self, label): return max(4, int(label['size'])//4)
    def _text_measure(self, label):
        font=self.font_for_export(label['size'],label.get('font','Arial Bold'));spacing=self._line_spacing(label)
        box=ImageDraw.Draw(Image.new('RGBA',(1,1))).multiline_textbbox((0,0),label['text'],font=font,anchor='mm',align='center',spacing=spacing)
        return int(box[2]-box[0]),int(box[3]-box[1])
    def _label_box(self, label):
        bw,bh=self._text_measure(label)
        width=max(65,bw+2*LABEL_PAD)
        height=max(28,bh+2*LABEL_PAD)
        if label.get('shape') in ('Right arrow','Left arrow'):width+=ARROW_TIP
        if label.get('shape') in ('Up arrow','Down arrow'):height+=ARROW_TIP
        return width,height
    def draw_export_label(self, image, label, progress=1.0, alpha=1.0):
        anim=label.get('animation','None');font=self.font_for_export(label['size'],label.get('font','Arial Bold'));spacing=self._line_spacing(label);w,h=self._label_box(label);opacity=int(max(0,min(100,label.get('opacity',100)))*2.55*alpha)
        if opacity<=0:return
        layer=Image.new('RGBA',(w+40,h+40),(0,0,0,0));draw=ImageDraw.Draw(layer);cx,cy=layer.width//2,layer.height//2
        def rgba(color,fallback):
            try:return ImageColor.getrgb(color)+(opacity,)
            except (ValueError,TypeError):return ImageColor.getrgb(fallback)+(opacity,)
        outline=label.get('outline','');draw.polygon(self.shape(label['shape'],cx,cy,w,h),fill=rgba(label['bg'],'#5B46C8'),outline=rgba(outline,'#000000') if outline else None,width=2)
        shown=label['text'][:max(1,int(len(label['text'])*progress))] if anim=='Typewriter' else label['text']
        tx,ty=cx,cy
        if label['shape']=='Right arrow':tx=cx-ARROW_TIP/2
        elif label['shape']=='Left arrow':tx=cx+ARROW_TIP/2
        elif label['shape']=='Up arrow':ty=cy+ARROW_TIP/2
        elif label['shape']=='Down arrow':ty=cy-ARROW_TIP/2
        draw.multiline_text((tx,ty),shown,font=font,fill=rgba(label['color'],'#FFFFFF'),anchor='mm',align='center',spacing=spacing,stroke_width=1 if outline else 0,stroke_fill=rgba(outline,'#000000') if outline else None)
        shadow=Image.new('RGBA',layer.size,(0,0,0,0));shadow.alpha_composite(layer,(3,3));shadow.putalpha(shadow.getchannel('A').point(lambda a:a//3));rotated=Image.alpha_composite(shadow,layer).rotate(-float(label.get('rotation',0)),resample=Image.Resampling.BICUBIC,expand=True)
        if anim=='Pop':
            scale=max(.05,.3+.7*progress);rotated=rotated.resize((max(1,int(rotated.width*scale)),max(1,int(rotated.height*scale))),Image.Resampling.LANCZOS)
        x=int(label['x']*image.width-rotated.width/2);y=int(label['y']*image.height-rotated.height/2)
        if anim=='Slide left':x-=int((1.0-progress)*image.width)
        elif anim=='Slide right':x+=int((1.0-progress)*image.width)
        image.paste(rotated,(x,y),rotated)
    def export_mp4(self):
        if not self.frames:return
        target=filedialog.asksaveasfilename(defaultextension='.mp4',filetypes=[("MP4 video","*.mp4"),("WebM video","*.webm"),("Animated GIF","*.gif")])
        if not target:return
        ff=FFMPEG if FFMPEG.exists() else shutil.which('ffmpeg')
        if not ff:return messagebox.showerror(APP,'FFmpeg was not found.')
        try:
            rate=max(.1,float(self.fps.get()));images=[self.frame_image(f) for f in self.frames]
            width=max(im.width for im in images);height=max(im.height for im in images);width+=width%2;height+=height%2
            with tempfile.TemporaryDirectory() as d:
                output_index=0
                for index,f in enumerate(self.frames):
                    steps=max(1,math.ceil(self.frame_duration(f)*rate))
                    for step in range(steps):
                        im=self.transition_image(index,step/rate)
                        canvas=Image.new('RGB',(width,height),'black');canvas.paste(im,((width-im.width)//2,(height-im.height)//2))
                        canvas.save(Path(d)/f'{output_index:05d}.png');output_index+=1
                command=[str(ff),'-y','-framerate',str(rate),'-i',str(Path(d)/'%05d.png')]
                if self.audio_path and self.audio_path.exists():command += ['-stream_loop','-1','-i',str(self.audio_path),'-shortest','-c:a','aac']
                suffix=Path(target).suffix.lower()
                if suffix=='.gif':command += ['-vf','fps='+str(rate)+',scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos',target]
                elif suffix=='.webm':command += ['-c:v','libvpx-vp9','-crf','32','-b:v','0',target]
                else:command += ['-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',target]
                subprocess.run(command,check=True,capture_output=True,text=True)
            self.status.set(f"MP4 exported: {Path(target).name}")
        except subprocess.CalledProcessError as e:
            detail=(e.stderr or e.stdout or str(e)).strip()
            messagebox.showerror(APP,f"MP4 export failed:\n{detail[-3000:]}")
        except Exception as e:messagebox.showerror(APP,f"MP4 export failed:\n{e}")
if __name__=='__main__':Animator().mainloop()
