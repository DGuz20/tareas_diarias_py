"""Tareas del Día: administrador de tareas pendientes para Windows.
Python 3.9+ y Tkinter (viene incluido). Sin dependencias externas.
Ejecutar:  python tareas_del_dia.py
Los datos se guardan en %APPDATA%\\TareasDelDia\\tareas.json
"""
import json
import os
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from tkinter import ttk

try:  # nitidez en pantallas de alta resolución (Windows)
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "TareasDelDia")
DATA_FILE = os.path.join(DATA_DIR, "tareas.json")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
PRIO = {"Alta": 0, "Media": 1, "Baja": 2}
PCOL = {"Alta": "#ff2e63", "Media": "#ffb800", "Baja": "#08c7d0"}
PH = "¿Qué tienes pendiente hoy?"
THEMES = {
    "dark": dict(bg="#0d0b14", panel="#161224", row="#1d1830", hover="#2a2145", fg="#ece8f8",
                 mut="#8f87aa", a="#ff2e63", ah="#ff5c85", b="#08f7fe", entry="#221b38"),
    "light": dict(bg="#f3eef6", panel="#e4dbee", row="#ffffff", hover="#ece2f5", fg="#1a1228",
                  mut="#5b4f74", a="#cf0f3d", ah="#e8335c", b="#006f82", entry="#ffffff"),
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tareas del Día")
        self.geometry("580x740")
        self.minsize(460, 540)
        self.theme, self.tasks, self.undo = "dark", [], []
        self.filter, self.new_prio, self.wrap = "all", "Media", 330
        self.prog = self.prog_t = 0.0
        self._anim = self._say = None
        self.ph = False
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *a: self.render())
        self.load()
        self.build()
        self.render()
        self.bind("<Control-z>", lambda e: self.undo_delete())
        self.bind("<Control-f>", lambda e: self.search_e.focus_set())
        self.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- datos ----------
    def load(self):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                d = json.load(f)
            self.theme = d.get("theme", "dark") if d.get("theme") in THEMES else "dark"
            self.tasks = [t for t in d.get("tasks", []) if {"id", "text", "done", "prio"} <= t.keys() and t["prio"] in PRIO]
            for t in self.tasks:
                t.setdefault("created", "")
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"theme": self.theme, "tasks": self.tasks}, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DATA_FILE)
        except OSError:
            self.say("No se pudo guardar el archivo")

    def commit(self):
        self.save()
        self.render()

    def on_close(self):
        self.save()
        self.destroy()

    # ---------- interfaz ----------
    def mkbtn(self, parent, text, cmd, bg=None, fg=None, hover=None, padx=14, pady=6):
        c = self.c
        bg, fg, hover = bg or c["panel"], fg or c["fg"], hover or c["hover"]
        b = tk.Label(parent, text=text, bg=bg, fg=fg, font=("Segoe UI", 10, "bold"), padx=padx, pady=pady, cursor="hand2")
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def build(self):
        c = self.c = THEMES[self.theme]
        self.configure(bg=c["bg"])
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("Vertical.TScrollbar", background=c["hover"], troughcolor=c["bg"], bordercolor=c["bg"],
                     arrowcolor=c["fg"], lightcolor=c["hover"], darkcolor=c["hover"])
        # cabecera
        head = tk.Frame(self, bg=c["bg"])
        head.pack(fill="x", padx=22, pady=(18, 0))
        tk.Label(head, text="Tareas de hoy", font=("Segoe UI", 22, "bold"), bg=c["bg"], fg=c["fg"]).pack(side="left")
        self.mkbtn(head, "☾" if self.theme == "dark" else "☀", self.toggle_theme, padx=10, pady=4).pack(side="right")
        n = datetime.now()
        tk.Label(self, text=f"{DIAS[n.weekday()].capitalize()}, {n.day} de {MESES[n.month - 1]} de {n.year}",
                 font=("Segoe UI", 10), bg=c["bg"], fg=c["mut"]).pack(anchor="w", padx=22)
        self.plabel = tk.Label(self, font=("Segoe UI", 10, "bold"), bg=c["bg"], fg=c["b"])
        self.plabel.pack(anchor="w", padx=22, pady=(10, 2))
        self.bar = tk.Canvas(self, height=10, bg=c["bg"], highlightthickness=0)
        self.bar.pack(fill="x", padx=22)
        self.bar.bind("<Configure>", lambda e: self.draw_bar())
        # agregar
        add = tk.Frame(self, bg=c["bg"])
        add.pack(fill="x", padx=22, pady=(14, 6))
        self.entry = tk.Entry(add, font=("Segoe UI", 12), bg=c["entry"], fg=c["fg"], insertbackground=c["fg"],
                              relief="flat", highlightthickness=2, highlightbackground=c["panel"], highlightcolor=c["b"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry.bind("<Return>", lambda e: self.add())
        self.entry.bind("<FocusIn>", self.ph_in)
        self.entry.bind("<FocusOut>", self.ph_out)
        self.pb = self.mkbtn(add, "", self.cycle_new, padx=10)
        self.pb.pack(side="left", padx=6, fill="y")
        self.mkbtn(add, "＋ Agregar", self.add, bg=c["a"], fg="#ffffff", hover=c["ah"]).pack(side="left", fill="y")
        self.style_new_prio()
        self.ph = False
        self.ph_out()
        # filtros y búsqueda
        fr = tk.Frame(self, bg=c["bg"])
        fr.pack(fill="x", padx=22, pady=(6, 6))
        self.fb = {}
        for k, txt in (("all", "Todas"), ("todo", "Pendientes"), ("done", "Hechas")):
            b = tk.Label(fr, text=txt, font=("Segoe UI", 10, "bold"), padx=12, pady=4, cursor="hand2")
            b.pack(side="left", padx=(0, 4))
            b.bind("<Button-1>", lambda e, k=k: self.set_filter(k))
            self.fb[k] = b
        self.search_e = tk.Entry(fr, textvariable=self.search, width=16, font=("Segoe UI", 10), bg=c["entry"], fg=c["fg"],
                                 insertbackground=c["fg"], relief="flat", highlightthickness=2,
                                 highlightbackground=c["panel"], highlightcolor=c["b"])
        self.search_e.pack(side="right", ipady=4)
        tk.Label(fr, text="🔍", bg=c["bg"], fg=c["mut"]).pack(side="right", padx=4)
        self.style_filters()
        # pie
        ft = tk.Frame(self, bg=c["bg"])
        ft.pack(side="bottom", fill="x", padx=22, pady=(4, 14))
        self.mkbtn(ft, "Limpiar completadas", self.clear_done, padx=10, pady=4).pack(side="left")
        self.mkbtn(ft, "↶ Deshacer", self.undo_delete, padx=10, pady=4).pack(side="left", padx=6)
        self.status = tk.Label(ft, text="", font=("Segoe UI", 9), bg=c["bg"], fg=c["mut"])
        self.status.pack(side="right")
        tk.Label(self, text="Clic en ○ para completar · doble clic para editar · clic en la prioridad para cambiarla",
                 font=("Segoe UI", 8), bg=c["bg"], fg=c["mut"]).pack(side="bottom", pady=(0, 2))
        # lista con scroll
        box = tk.Frame(self, bg=c["bg"])
        box.pack(fill="both", expand=True, padx=(22, 16), pady=(0, 6))
        self.canvas = tk.Canvas(box, bg=c["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.rows = tk.Frame(self.canvas, bg=c["bg"])
        win = self.canvas.create_window((0, 0), window=self.rows, anchor="nw")
        self.rows.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: (self.canvas.itemconfig(win, width=e.width),
                                                   setattr(self, "wrap", max(180, e.width - 200))))

    def ph_in(self, e=None):
        if self.ph:
            self.entry.delete(0, "end")
            self.entry.config(fg=self.c["fg"])
            self.ph = False

    def ph_out(self, e=None):
        if not self.entry.get():
            self.entry.insert(0, PH)
            self.entry.config(fg=self.c["mut"])
            self.ph = True

    def new_text(self):
        return "" if self.ph else self.entry.get().strip()

    def style_new_prio(self):
        self.pb.config(text=f"● {self.new_prio}", fg=PCOL[self.new_prio])

    def style_filters(self):
        c = self.c
        for k, b in self.fb.items():
            on = k == self.filter
            b.config(bg=c["a"] if on else c["panel"], fg="#ffffff" if on else c["mut"])

    def say(self, msg):
        if self._say:
            self.after_cancel(self._say)
        self.status.config(text=msg)
        self._say = self.after(4000, lambda: self.status.config(text=""))

    # ---------- progreso animado ----------
    def draw_bar(self):
        try:
            c, w = self.c, self.bar.winfo_width()
            self.bar.delete("all")
            self.bar.create_rectangle(0, 0, w, 10, fill=c["panel"], outline="")
            full = self.tasks and self.prog_t >= 1
            self.bar.create_rectangle(0, 0, w * self.prog, 10, fill=c["b"] if full else c["a"], outline="")
        except tk.TclError:
            pass

    def animate(self):
        if self._anim:
            self.after_cancel(self._anim)
            self._anim = None
        diff = self.prog_t - self.prog
        if abs(diff) < 0.004:
            self.prog = self.prog_t
        else:
            self.prog += diff * 0.2
            self._anim = self.after(16, self.animate)
        self.draw_bar()

    # ---------- acciones ----------
    def add(self):
        text = self.new_text()
        if not text:
            self.entry.config(highlightbackground=self.c["a"], highlightcolor=self.c["a"])
            self.after(350, lambda: self.entry.config(highlightbackground=self.c["panel"], highlightcolor=self.c["b"]))
            self.entry.focus_set()
            return
        nid = max([t["id"] for t in self.tasks], default=0) + 1
        self.tasks.append({"id": nid, "text": text, "done": False, "prio": self.new_prio,
                           "created": datetime.now().strftime("%d/%m %H:%M")})
        self.entry.delete(0, "end")
        self.ph = False
        self.entry.focus_set()
        self.commit()

    def cycle_new(self):
        order = list(PRIO)
        self.new_prio = order[(order.index(self.new_prio) + 1) % 3]
        self.style_new_prio()

    def toggle(self, t):
        t["done"] = not t["done"]
        self.commit()

    def cycle_prio(self, t):
        order = list(PRIO)
        t["prio"] = order[(order.index(t["prio"]) + 1) % 3]
        self.commit()

    def delete(self, t):
        i = self.tasks.index(t)
        self.tasks.pop(i)
        self.undo.append([(i, t)])
        self.say("Tarea eliminada · Ctrl+Z para deshacer")
        self.commit()

    def clear_done(self):
        items = [(i, t) for i, t in enumerate(self.tasks) if t["done"]]
        if not items:
            self.say("No hay tareas completadas")
            return
        self.tasks = [t for t in self.tasks if not t["done"]]
        self.undo.append(items)
        self.say(f"{len(items)} eliminadas · Ctrl+Z para deshacer")
        self.commit()

    def undo_delete(self):
        if not self.undo:
            self.say("Nada que deshacer")
            return
        for i, t in sorted(self.undo.pop(), key=lambda x: x[0]):
            self.tasks.insert(min(i, len(self.tasks)), t)
        self.say("Tarea restaurada")
        self.commit()

    def set_filter(self, k):
        self.filter = k
        self.style_filters()
        self.render()

    def toggle_theme(self):
        txt = self.new_text()
        if self._anim:
            self.after_cancel(self._anim)
            self._anim = None
        for w in self.winfo_children():
            w.destroy()
        self.theme = "light" if self.theme == "dark" else "dark"
        self.build()
        if txt:
            self.ph_in()
            self.entry.insert(0, txt)
        self.render()
        self.save()

    def edit(self, t, lab, sub):
        c = self.c
        e = tk.Entry(lab.master, font=("Segoe UI", 12), bg=c["entry"], fg=c["fg"], insertbackground=c["fg"], relief="flat",
                     highlightthickness=2, highlightbackground=c["b"], highlightcolor=c["a"])
        e.insert(0, t["text"])
        e.pack(fill="x", before=lab)
        lab.pack_forget()
        fin = [False]

        def finish(save=True):
            if fin[0]:
                return
            fin[0] = True
            v = e.get().strip()
            if save and v and v != t["text"]:
                t["text"] = v
                self.commit()
            else:
                self.render()

        e.bind("<Return>", lambda ev: finish())
        e.bind("<Escape>", lambda ev: finish(False))
        e.bind("<FocusOut>", lambda ev: finish())
        e.focus_set()
        e.select_range(0, "end")

    # ---------- lista ----------
    def render(self):
        c = self.c
        for w in self.rows.winfo_children():
            w.destroy()
        q = self.search.get().strip().lower()
        items = [t for t in self.tasks
                 if (self.filter == "all" or (self.filter == "todo") != t["done"]) and q in t["text"].lower()]
        items.sort(key=lambda t: (t["done"], PRIO[t["prio"]], t["id"]))
        if not items:
            msg = "Nada por aquí.\n¡Agrega tu primera tarea!" if not self.tasks else "Sin resultados."
            tk.Label(self.rows, text=msg, font=("Segoe UI", 12), bg=c["bg"], fg=c["mut"], pady=40).pack(fill="x")
        for t in items:
            self.row(t)
        n, d = len(self.tasks), sum(t["done"] for t in self.tasks)
        self.plabel.config(text="Sin tareas todavía" if not n else
                           ("🎉 ¡Día completado!  " if d == n else "") + f"{d} de {n} completadas")
        self.prog_t = d / n if n else 0.0
        self.animate()

    def row(self, t):
        c, done, rb = self.c, t["done"], self.c["row"]
        r = tk.Frame(self.rows, bg=rb)
        r.pack(fill="x", pady=3, padx=(0, 6))
        tk.Frame(r, bg=c["mut"] if done else PCOL[t["prio"]], width=5).pack(side="left", fill="y")
        chk = tk.Label(r, text="●" if done else "○", font=("Segoe UI", 16), bg=rb, cursor="hand2", padx=10,
                       fg=c["b"] if done else c["mut"])
        chk.pack(side="left")
        chk.bind("<Button-1>", lambda e: self.toggle(t))
        body = tk.Frame(r, bg=rb)
        body.pack(side="left", fill="x", expand=True, pady=8)
        font = tkfont.Font(family="Segoe UI", size=12, overstrike=done)
        lab = tk.Label(body, text=t["text"], font=font, bg=rb, fg=c["mut"] if done else c["fg"], anchor="w",
                       justify="left", wraplength=self.wrap)
        lab.pack(fill="x")
        sub = tk.Label(body, text=f"{t['prio']} · {t['created']}", font=("Segoe UI", 8), bg=rb, anchor="w",
                       fg=c["mut"] if done else PCOL[t["prio"]], cursor="hand2")
        sub.pack(fill="x")
        sub.bind("<Button-1>", lambda e: self.cycle_prio(t))
        lab.bind("<Double-Button-1>", lambda e: self.edit(t, lab, sub))
        btns = tk.Frame(r, bg=rb)
        btns.pack(side="right", padx=6)
        for sym, fn, hc in (("✎", lambda: self.edit(t, lab, sub), c["b"]), ("✕", lambda: self.delete(t), c["a"])):
            b = tk.Label(btns, text=sym, font=("Segoe UI", 12), bg=rb, fg=c["mut"], cursor="hand2", padx=6)
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, fn=fn: fn())
            b.bind("<Enter>", lambda e, b=b, hc=hc: b.config(fg=hc))
            b.bind("<Leave>", lambda e, b=b: b.config(fg=c["mut"]))
        ws = [r, chk, body, lab, sub, btns, *btns.winfo_children()]

        def hov(on):
            for w in ws:
                try:
                    w.config(bg=c["hover"] if on else rb)
                except tk.TclError:
                    pass

        for w in ws:
            w.bind("<Enter>", lambda e: hov(True), add="+")
            w.bind("<Leave>", lambda e: hov(False), add="+")


if __name__ == "__main__":
    App().mainloop()
