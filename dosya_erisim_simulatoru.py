import customtkinter as ctk
from tkinter import messagebox
import json
import os
from datetime import datetime

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

DATA_FILE = "filesystem_data_modern.json"
RWX_TABLE = ["---", "--x", "-w-", "-wx", "r--", "r-x", "rw-", "rwx"]
PERM_BITS = {"r": 4, "w": 2, "x": 1}


class User:

    def __init__(self, username, groups):
        self.username = username
        self.groups = groups  # örn: ["ogrenci", "proje_ekibi"]

    def label(self):
        # Kullanıcı seçim menüsünde ve seçilen etiketten kullanıcı adını
        # geri ayrıştırmak için kullanılıyor (on_user_change). Gerekli.
        return f"{self.username} ({', '.join(self.groups)})"


class File:
    

    def __init__(self, filename, owner, group, permissions, content=""):
        self.filename = filename
        self.owner = owner
        self.group = group
        self.permissions = permissions  # örn: "755"
        self.content = content
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.accessed_at = datetime.now()

    @property
    def size(self):
        # İçerikten her zaman yeniden hesaplanır; ayrıca saklanmaz.
        # Böylece content değişip size güncellenmeyi unutursa oluşacak
        # tutarsızlık riski tamamen ortadan kalkar.
        return len(self.content.encode("utf-8"))

    def check_permission(self, user, action):
       
        if user.username == "root":
            return True

        required = PERM_BITS[action]

        if user.username == self.owner.username:
            digit = self.permissions[0]
        elif self.group in user.groups:
            digit = self.permissions[1]
        else:
            digit = self.permissions[2]

        return (int(digit) & required) != 0

    def rwx(self):
        try:
            return "".join(RWX_TABLE[int(d)] for d in self.permissions)
        except (ValueError, IndexError):
            return "?????????"

    def human_size(self):
        s = self.size
        if s < 1024:
            return f"{s} B"
        if s < 1024 * 1024:
            return f"{s / 1024:.1f} KB"
        return f"{s / (1024 * 1024):.1f} MB"

    def to_dict(self):
        return {
            "filename": self.filename,
            "owner": self.owner.username,
            "group": self.group,
            "permissions": self.permissions,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
        }

    @staticmethod
    def from_dict(data, users_by_name):
        owner = users_by_name.get(data["owner"])
        if not owner:
            return None
        f = File(data["filename"], owner, data["group"], data["permissions"], data["content"])
        f.created_at = datetime.fromisoformat(data["created_at"])
        f.modified_at = datetime.fromisoformat(data["modified_at"])
        f.accessed_at = datetime.fromisoformat(data["accessed_at"])
        return f


# ==================== ANA UYGULAMA ====================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dosya Erişim İzinleri Simülatörü")
        self.geometry("1260x820")
        self.minsize(1080, 720)
        self.configure(fg_color=("#eef2f7", "#111827"))

        self.users = []
        self.files = []
        self.filtered_files = []
        self.pending_logs = []

        self.load_or_create_data()

        self.current_user = self.users[0]
        self.current_file = self.files[0] if self.files else None

        self.build_ui()
        self.filter_files()
        self.update_info()
        self.update_statistics()

        for level, msg in self.pending_logs:
            self.log(level, msg)
        self.pending_logs.clear()

   

    def load_or_create_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.users = [User(u["username"], u["groups"]) for u in data["users"]]
                users_by_name = {u.username: u for u in self.users}
                self.files = [f for f in (File.from_dict(fd, users_by_name) for fd in data["files"]) if f]
                self.pending_logs.append(("INFO", "Veriler dosyadan yüklendi."))
                return
            except Exception as e:
                self.pending_logs.append(("ERROR", f"Veri yüklenemedi, varsayılanlar oluşturuluyor: {e}"))

        self.create_default_data()
        self.save_data(quiet=True)

    def create_default_data(self):
        self.users = [
            User("root", ["root", "admin"]),
            User("esma", ["proje_ekibi", "yonetim"]),
            User("sumeyye", ["proje_ekibi"]),
            User("imge", ["proje_ekibi"]),
            User("cagla", ["proje_ekibi"]),
            User("busra", ["proje_ekibi"]),
            User("asli", ["proje_ekibi"]),
            User("emir", ["proje_ekibi", "yonetim"]),
        ]
        u = {usr.username: usr for usr in self.users}
        self.files = [
            File("odev.txt", u["esma"], "proje_ekibi", "755", "Esma'nın ödev dosyası.\nProje planlama notları."),
            File("rapor.txt", u["sumeyye"], "proje_ekibi", "640", "Sümeyye'nin hazırladığı proje raporu."),
            File("sunum.txt", u["imge"], "proje_ekibi", "750", "İmge'nin hazırladığı sunum içeriği."),
            File("kod.py", u["cagla"], "proje_ekibi", "770", "print('Merhaba Dünya!')\nprint('Python çalışıyor!')"),
            File("notlar.txt", u["busra"], "proje_ekibi", "644", "Büşra'nın toplantı notları."),
            File("butce.txt", u["asli"], "yonetim", "600", "GİZLİ - Aslı'nın hazırladığı bütçe tablosu."),
            File("planlama.md", u["emir"], "yonetim", "640", "# Planlama\nEmir'in hazırladığı yol haritası."),
            File("sistem.log", u["root"], "root", "600", "Sistem günlüğü - sadece root okuyabilir."),
        ]
        self.pending_logs.append(("INFO", "Varsayılan ekip verileri oluşturuldu."))

    def save_data(self, quiet=False):
        try:
            data = {
                "users": [{"username": u.username, "groups": u.groups} for u in self.users],
                "files": [f.to_dict() for f in self.files],
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if not quiet:
                self.log("INFO", "Veriler kaydedildi.")
        except Exception as e:
            self.log("ERROR", f"Kaydetme hatası: {e}")

    # Arayüz

    def build_ui(self):
        self.build_top_bar()

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=22, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1, minsize=390)
        content.grid_columnconfigure(1, weight=2, minsize=590)
        content.grid_rowconfigure(0, weight=1)

        self.build_file_panel(content)
        self.build_detail_panel(content)
        self.build_log_panel()

    def build_top_bar(self):
        bar = ctk.CTkFrame(self, corner_radius=12, fg_color=("#ffffff", "#1f2937"))
        bar.pack(fill="x", padx=22, pady=18)
        bar.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(bar, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w", padx=18, pady=14)
        ctk.CTkLabel(
            title_box,
            text="Dosya Erişim İzinleri",
            font=("Segoe UI", 24, "bold"),
            text_color=("#111827", "#f9fafb"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Kullanıcı, grup ve rwx izinlerini görsel olarak test et.",
            font=("Segoe UI", 12),
            text_color=("#64748b", "#cbd5e1"),
        ).pack(anchor="w", pady=(2, 0))

        user_box = ctk.CTkFrame(bar, fg_color="transparent")
        user_box.grid(row=0, column=1, sticky="e", padx=18, pady=14)
        ctk.CTkLabel(user_box, text="Aktif kullanıcı", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.user_menu = ctk.CTkOptionMenu(
            user_box,
            values=[u.label() for u in self.users],
            command=self.on_user_change,
            width=230,
            height=34,
            fg_color="#2563eb",
            button_color="#1d4ed8",
            button_hover_color="#1e40af",
        )
        self.user_menu.set(self.current_user.label())
        self.user_menu.pack(anchor="w", pady=(4, 0))

        actions = ctk.CTkFrame(bar, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=(0, 18), pady=14)
        ctk.CTkButton(actions, text="+ Dosya", command=self.create_new_file, width=96, height=34,
                      fg_color="#059669", hover_color="#047857").pack(side="left", padx=4)
        ctk.CTkButton(actions, text="+ Kullanıcı", command=self.create_new_user, width=112, height=34,
                      fg_color="#0f766e", hover_color="#115e59").pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Kullanıcı Sil", command=self.delete_user, width=112, height=34,
                      fg_color="#f97316", hover_color="#ea580c").pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Dosya Sil", command=self.delete_file, width=96, height=34,
                      fg_color="#dc2626", hover_color="#b91c1c").pack(side="left", padx=4)

    def build_file_panel(self, parent):
        left = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#ffffff", "#1f2937"))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        header = ctk.CTkFrame(left, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="Dosyalar", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.file_count_label = ctk.CTkLabel(header, text="", font=("Segoe UI", 12),
                                             text_color=("#64748b", "#cbd5e1"))
        self.file_count_label.pack(side="right")

        search_row = ctk.CTkFrame(left, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=(0, 10))
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="Dosya adı ara...", height=36)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_files())

        self.filter_menu = ctk.CTkOptionMenu(
            search_row,
            values=["Tümü", "Okunabilir", "Yazılabilir", "Çalıştırılabilir", "Bana Ait"],
            command=lambda _: self.filter_files(),
            width=145,
            height=36,
            fg_color="#475569",
            button_color="#334155",
            button_hover_color="#1e293b",
        )
        self.filter_menu.set("Tümü")
        self.filter_menu.pack(side="left")

        self.file_list_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.file_list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def build_detail_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        detail = ctk.CTkFrame(right, corner_radius=12, fg_color=("#ffffff", "#1f2937"))
        detail.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        header = ctk.CTkFrame(detail, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(header, text="Dosya Detayı", font=("Segoe UI", 18, "bold")).pack(side="left")

        self.info_label = ctk.CTkLabel(
            detail,
            text="",
            font=("Segoe UI", 13),
            justify="left",
            anchor="w",
            text_color=("#1f2937", "#e5e7eb"),
        )
        self.info_label.pack(fill="x", padx=18, pady=(0, 12), anchor="w")

        ctk.CTkLabel(detail, text="İzin Haritası", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18)
        self.perm_display_frame = ctk.CTkFrame(detail, corner_radius=10, fg_color=("#f8fafc", "#111827"))
        self.perm_display_frame.pack(fill="x", padx=18, pady=(6, 14))

        action_row = ctk.CTkFrame(detail, fg_color="transparent")
        action_row.pack(fill="x", padx=18, pady=(0, 12))
        ctk.CTkButton(action_row, text="Oku", height=40, fg_color="#16a34a", hover_color="#15803d",
                      command=lambda: self.do_action("r")).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(action_row, text="Düzenle", height=40, fg_color="#d97706", hover_color="#b45309",
                      command=lambda: self.do_action("w")).pack(side="left", expand=True, fill="x", padx=6)
        ctk.CTkButton(action_row, text="Çalıştır", height=40, fg_color="#7c3aed", hover_color="#6d28d9",
                      command=lambda: self.do_action("x")).pack(side="left", expand=True, fill="x", padx=(6, 0))

        admin_row = ctk.CTkFrame(detail, corner_radius=10, fg_color=("#f8fafc", "#111827"))
        admin_row.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkLabel(admin_row, text="chmod", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(12, 6), pady=12)
        self.chmod_entry = ctk.CTkEntry(admin_row, width=74, placeholder_text="755", height=32)
        self.chmod_entry.pack(side="left", padx=(0, 8), pady=12)
        ctk.CTkButton(admin_row, text="Uygula", command=self.apply_chmod, width=80, height=32,
                      fg_color="#2563eb", hover_color="#1d4ed8").pack(side="left", padx=(0, 18), pady=12)

        ctk.CTkLabel(admin_row, text="chown", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 6), pady=12)
        self.chown_menu = ctk.CTkOptionMenu(admin_row, values=[u.username for u in self.users], width=125, height=32)
        self.chown_menu.pack(side="left", padx=(0, 8), pady=12)
        ctk.CTkButton(admin_row, text="Uygula", command=self.apply_chown, width=80, height=32,
                      fg_color="#4f46e5", hover_color="#4338ca").pack(side="left", pady=12)

        self.build_stats_panel(right)

    def build_stats_panel(self, parent):
        stats = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#ffffff", "#1f2937"))
        stats.grid(row=1, column=0, sticky="ew")
        ctk.CTkLabel(stats, text="Özet", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(14, 8))

        grid = ctk.CTkFrame(stats, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

        items = [
            ("Toplam Dosya", "total_files"),
            ("Sahip Olduğum", "owned_files"),
            ("Okunabilir", "readable"),
            ("Yazılabilir", "writable"),
            ("Çalıştırılabilir", "executable"),
            ("Toplam Boyut", "total_size"),
        ]
        self.stats_labels = {}
        for i, (text, key) in enumerate(items):
            box = ctk.CTkFrame(grid, corner_radius=10, fg_color=("#f1f5f9", "#111827"))
            box.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="ew")
            ctk.CTkLabel(box, text=text, font=("Segoe UI", 11),
                         text_color=("#64748b", "#cbd5e1")).pack(anchor="w", padx=10, pady=(8, 0))
            self.stats_labels[key] = ctk.CTkLabel(box, text="0", font=("Segoe UI", 18, "bold"))
            self.stats_labels[key].pack(anchor="w", padx=10, pady=(0, 8))

    def build_log_panel(self):
        # Günlük alanı pencere yüksekliği azaldığında tek satıra sıkışmasın.
        frame = ctk.CTkFrame(
            self,
            height=155,
            corner_radius=12,
            fg_color=("#ffffff", "#1f2937"),
        )
        frame.pack(fill="x", padx=22, pady=(0, 14))
        frame.pack_propagate(False)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(header, text="Sistem Günlüğü", font=("Segoe UI", 14, "bold")).pack(side="left")

        ctk.CTkButton(
            header,
            text="Temizle",
            width=86,
            height=30,
            fg_color="#64748b",
            hover_color="#475569",
            command=lambda: self.log_text.delete("0.0", "end"),
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            frame,
            height=85,
            font=("Consolas", 12),
            corner_radius=10,
        )
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    def update_permission_display(self, permissions):
        for w in self.perm_display_frame.winfo_children():
            w.destroy()

        try:
            perms = [RWX_TABLE[int(d)] for d in permissions]
        except (ValueError, IndexError):
            ctk.CTkLabel(self.perm_display_frame, text="Geçersiz izin formatı").pack(pady=12)
            return

        row = ctk.CTkFrame(self.perm_display_frame, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=10)
        bit_colors = {"r": "#16a34a", "w": "#2563eb", "x": "#d97706"}

        for label, digit, perm_str in zip(["Sahip", "Grup", "Diğer"], permissions, perms):
            group = ctk.CTkFrame(row, fg_color="transparent")
            group.pack(side="left", expand=True, fill="x", padx=6)
            ctk.CTkLabel(group, text=f"{label} ({digit})", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            chars_row = ctk.CTkFrame(group, fg_color="transparent")
            chars_row.pack(anchor="w", pady=(6, 0))
            for ch in perm_str:
                active = ch != "-"
                ctk.CTkLabel(
                    chars_row,
                    text=ch if active else "-",
                    width=31,
                    height=30,
                    corner_radius=8,
                    fg_color=bit_colors.get(ch, "#cbd5e1") if active else ("#e5e7eb", "#374151"),
                    text_color="white" if active else ("#64748b", "#9ca3af"),
                    font=("Segoe UI", 13, "bold"),
                ).pack(side="left", padx=2)

    # Filtreleme / Listeleme

    def filter_files(self):
        term = self.search_entry.get().lower().strip()
        mode = self.filter_menu.get()

        def passes(f):
            if term and term not in f.filename.lower():
                return False
            if mode == "Okunabilir" and not f.check_permission(self.current_user, "r"):
                return False
            if mode == "Yazılabilir" and not f.check_permission(self.current_user, "w"):
                return False
            if mode == "Çalıştırılabilir" and not f.check_permission(self.current_user, "x"):
                return False
            if mode == "Bana Ait" and f.owner.username != self.current_user.username:
                return False
            return True

        self.filtered_files = [f for f in self.files if passes(f)]
        self.file_count_label.configure(text=f"{len(self.filtered_files)}/{len(self.files)} dosya")
        self.refresh_file_list()

    def refresh_file_list(self):
        for w in self.file_list_frame.winfo_children():
            w.destroy()

        colors = {
            ".py": "#2563eb",
            ".sh": "#2563eb",
            ".txt": "#16a34a",
            ".md": "#0f766e",
            ".pdf": "#dc2626",
            ".log": "#64748b",
        }

        for f in self.filtered_files:
            ext = os.path.splitext(f.filename)[1]
            color = colors.get(ext, "#475569")
            is_owned = f.owner.username == self.current_user.username
            is_selected = self.current_file and f.filename == self.current_file.filename

            btn = ctk.CTkButton(
                self.file_list_frame,
                text=f"{f.filename}\n{f.owner.username} - {f.group} - {f.permissions} ({f.rwx()})",
                anchor="w",
                height=58,
                font=("Segoe UI", 12, "bold"),
                fg_color="#1d4ed8" if is_selected else color,
                hover_color="#1e40af" if is_selected else "#334155",
                text_color="white",
                border_width=2 if (is_owned or is_selected) else 0,
                border_color="#facc15" if is_owned else "#93c5fd",
                command=lambda name=f.filename: self.select_file(name),
            )
            btn.pack(fill="x", pady=5, padx=4)

    # İstatistikler

    def update_statistics(self):
        u = self.current_user
        total_size = sum(f.size for f in self.files)
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"

        self.stats_labels["total_files"].configure(text=str(len(self.files)))
        self.stats_labels["owned_files"].configure(
            text=str(sum(1 for f in self.files if f.owner.username == u.username)))
        self.stats_labels["readable"].configure(
            text=str(sum(1 for f in self.files if f.check_permission(u, "r"))))
        self.stats_labels["writable"].configure(
            text=str(sum(1 for f in self.files if f.check_permission(u, "w"))))
        self.stats_labels["executable"].configure(
            text=str(sum(1 for f in self.files if f.check_permission(u, "x"))))
        self.stats_labels["total_size"].configure(text=size_str)

    # - Kullanıcı / Dosya Seçimi

    def log(self, level, message):
        if not hasattr(self, "log_text"):
            self.pending_logs.append((level, message))
            return
        icon = {"INFO": "INFO", "SUCCESS": "OK", "ERROR": "HATA", "WARNING": "UYARI"}.get(level, "LOG")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {icon:<5} {message}\n")
        self.log_text.see("end-1c")

    def on_user_change(self, choice):
        username = choice.split(" ")[0]
        self.current_user = next(u for u in self.users if u.username == username)
        self.log("INFO", f"Kullanıcı değiştirildi: {self.current_user.username}")
        self.filter_files()
        self.update_info()
        self.update_statistics()

    def select_file(self, filename):
        self.current_file = next((f for f in self.files if f.filename == filename), None)
        self.log("INFO", f"Dosya seçildi: {filename}")
        self.update_info()
        self.refresh_file_list()

    def update_info(self):
        if not self.current_file:
            self.info_label.configure(text="Gösterilecek dosya yok.")
            return

        f = self.current_file
        preview = f.content[:180] + ("..." if len(f.content) > 180 else "")
        info = (
            f"Dosya Adı      {f.filename}\n"
            f"Sahibi         {f.owner.username}\n"
            f"Grup           {f.group}\n"
            f"Boyut          {f.human_size()}\n"
            f"İzinler       {f.permissions}  ({f.rwx()})\n"
            f"Oluşturulma    {f.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"Değiştirilme  {f.modified_at.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"Son Erişim     {f.accessed_at.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"İçerik Önizleme\n{preview}"
        )
        self.info_label.configure(text=info)

        self.chmod_entry.delete(0, "end")
        self.chmod_entry.insert(0, f.permissions)
        self.chown_menu.set(f.owner.username)
        self.update_permission_display(f.permissions)

    # Kullanıcı Yönetimi

    def create_new_user(self):
        username = ctk.CTkInputDialog(
            text="Kullanıcı adını girin (boşluksuz, küçük harf):", title="👤 Yeni Kullanıcı"
        ).get_input()
        if not username:
            return
        username = username.strip().lower()

        if not username or " " in username:
            messagebox.showerror("Hata", "Kullanıcı adı boşluk içeremez!")
            return
        if any(u.username == username for u in self.users):
            messagebox.showerror("Hata", f"'{username}' adında bir kullanıcı zaten var!")
            return

        groups_input = ctk.CTkInputDialog(
            text="Grupları virgülle ayırarak girin (örn: proje_ekibi, yonetim):",
            title="Kullanıcı Grupları",
        ).get_input()
     
        groups = [g.strip().lower() for g in (groups_input or "").split(",") if g.strip()]
        if not groups:
            groups = ["kullanicilar"]

        new_user = User(username, groups)
        self.users.append(new_user)

        self.user_menu.configure(values=[u.label() for u in self.users])
        self.chown_menu.configure(values=[u.username for u in self.users])

        self.save_data()
        self.log("SUCCESS", f"Yeni kullanıcı eklendi: {username} ({', '.join(groups)})")

    def delete_user(self):
        """Kullanıcı silme özelliği"""
        if not self.users:
            messagebox.showwarning("Uyarı", "Silinecek kullanıcı yok!")
            return

        user_names = [u.username for u in self.users]
        delete_dialog = ctk.CTkInputDialog(
            text=f"Mevcut kullanıcılar: {', '.join(user_names)}\n\nSilinecek kullanıcı adını girin:",
            title="👤 Kullanıcı Sil"
        )
        username_to_delete = delete_dialog.get_input()

        if not username_to_delete:
            return

        username_to_delete = username_to_delete.strip().lower()

        if username_to_delete == "root":
            messagebox.showerror("Hata", "root kullanıcısı silinemez!")
            return

        user_to_delete = next((u for u in self.users if u.username == username_to_delete), None)
        if not user_to_delete:
            messagebox.showerror("Hata", f"'{username_to_delete}' adında bir kullanıcı bulunamadı!")
            return

        if len(self.users) <= 1:
            messagebox.showerror("Hata", "Son kalan kullanıcı silinemez!")
            return

        owned_files = [f for f in self.files if f.owner.username == username_to_delete]
        if owned_files:
            files_list = "\n".join(f"  - {f.filename}" for f in owned_files)
            confirm = messagebox.askyesno(
                "Dosya Sahipliği Uyarısı",
                f"{username_to_delete} kullanıcısının sahibi olduğu dosyalar:\n{files_list}\n\n"
                "Bu kullanıcı silinirse, dosyaların sahibi root olarak değiştirilecektir.\n"
                "Devam etmek istediğinize emin misiniz?"
            )
            if not confirm:
                return

            root_user = next((u for u in self.users if u.username == "root"), None)
            if root_user:
                for f in owned_files:
                    f.owner = root_user
                    f.modified_at = datetime.now()
                self.log("INFO", f"{len(owned_files)} dosyanın sahibi root olarak değiştirildi")

        self.users.remove(user_to_delete)

        if self.current_user.username == username_to_delete:
            self.current_user = next((u for u in self.users if u.username == "root"), self.users[0])
            self.user_menu.set(self.current_user.label())

        self.user_menu.configure(values=[u.label() for u in self.users])
        self.chown_menu.configure(values=[u.username for u in self.users])

        self.save_data()
        self.filter_files()
        self.update_info()
        self.update_statistics()
        self.log("SUCCESS", f"Kullanıcı silindi: {username_to_delete}")

        messagebox.showinfo("Başarılı", f"'{username_to_delete}' kullanıcısı silindi.")

    # Dosya Yönetimi

    def create_new_file(self):
        filename = ctk.CTkInputDialog(text="Dosya adını girin:", title="Yeni Dosya").get_input()
        if filename is None:
            return

        filename = filename.strip()
        if not filename:
            messagebox.showerror("Hata", "Dosya adı boş bırakılamaz!")
            return

        if any(f.filename == filename for f in self.files):
            messagebox.showerror("Hata", "Bu isimde bir dosya zaten var!")
            return

        perms = ctk.CTkInputDialog(text="İzinleri girin (örn: 755):", title="İzinler").get_input() or "755"
        if not (len(perms) == 3 and all(c in "01234567" for c in perms)):
            perms = "755"
            messagebox.showinfo("Bilgi", "Geçersiz izin, varsayılan 755 kullanıldı.")

        # Kullanıcının birden fazla grubu varsa hangisiyle oluşturulacağını sorulmalı
        groups = self.current_user.groups
        if len(groups) > 1:
            group_dialog = ctk.CTkInputDialog(
                text=f"Grup seçin ({', '.join(groups)}):", title="Dosya Grubu"
            ).get_input()
            # Önce normalize et (küçük harf + boşluksuz), sonra üyelik kontrolü yap. hepsi uyumlu olmalı
            chosen = group_dialog.strip().lower() if group_dialog else ""
            group = chosen if chosen in groups else groups[0]
        else:
            group = groups[0] if groups else "users"

        new_file = File(filename, self.current_user, group, perms, f"Yeni dosya: {filename}")
        self.files.append(new_file)
        self.current_file = new_file
        self.save_data()
        self.filter_files()
        self.update_info()
        self.update_statistics()
        self.log("SUCCESS", f"Yeni dosya oluşturuldu: {filename}")

    def delete_file(self):
        f = self.current_file
        if not f:
            return
        if self.current_user.username not in (f.owner.username, "root"):
            messagebox.showerror("Yetki Hatası", "Sadece dosya sahibi veya root dosya silebilir!")
            self.log("ERROR", f"{self.current_user.username}, '{f.filename}' dosyasını silmeye çalıştı - yetki yok")
            return

        if not messagebox.askyesno("Dosya Sil", f"'{f.filename}' silinsin mi?"):
            return

        self.files.remove(f)
        self.current_file = self.files[0] if self.files else None
        self.save_data()
        self.filter_files()
        self.update_info()
        self.update_statistics()
        self.log("SUCCESS", f"Dosya silindi: {f.filename}")

    # -------------------- chmod / chown --------------------

    def apply_chmod(self):
        f = self.current_file
        if not f:
            return

        # Yetki kontrolü ÖNCE yapılıyor: yetkisiz kullanıcı format hatasını
        # bile görmemeli, öncelik her zaman yetki kontrolünde olmalı.
        if self.current_user.username not in (f.owner.username, "root"):
            messagebox.showerror("Yetki Hatası", "Sadece dosya sahibi veya root chmod yapabilir!")
            self.log("ERROR", f"{self.current_user.username}, chmod için yetkisiz")
            return

        new_perm = self.chmod_entry.get().strip()
        if not (len(new_perm) == 3 and all(c in "01234567" for c in new_perm)):
            messagebox.showwarning("Geçersiz İzin", "3 haneli oktal sayı girin (örn: 755)")
            return

        old = f.permissions
        f.permissions = new_perm
        f.modified_at = datetime.now()
        self.save_data()
        self.filter_files()
        self.update_info()
        self.update_statistics()
        self.log("SUCCESS", f"chmod {old} → {new_perm} ({f.filename})")

    def apply_chown(self):
        f = self.current_file
        if not f:
            return

        if self.current_user.username != "root":
            messagebox.showerror("Yetki Hatası", "Sadece root chown yapabilir!")
            self.log("ERROR", f"{self.current_user.username}, chown için yetkisiz")
            return

        new_owner = next((u for u in self.users if u.username == self.chown_menu.get()), None)
        if not new_owner:
            return

        old_owner = f.owner.username
        f.owner = new_owner
        f.modified_at = datetime.now()
        self.save_data()
        self.filter_files()
        self.update_info()
        self.update_statistics()
        self.log("SUCCESS", f"chown {old_owner} → {new_owner.username} ({f.filename})")

    # -------------------- Oku / Yaz / Çalıştır --------------------

    def do_action(self, action):
        f = self.current_file
        user = self.current_user
        if not f:
            return

        names = {"r": "okuma", "w": "düzenleme", "x": "çalıştırma"}

        if not f.check_permission(user, action):
            self.log("ERROR", f"{user.username}, '{f.filename}' üzerinde {names[action]} yapamadı - izin yok")
            messagebox.showerror(
                "⛔ Erişim Engellendi",
                f"{names[action].capitalize()} yetkiniz yok!\nDosya: {f.filename}\n"
                f"İzinler: {f.permissions} ({f.rwx()})\nSahip: {f.owner.username}",
            )
            return

        if action == "r":
            f.accessed_at = datetime.now()
            self.save_data(quiet=True)
            self.update_info()
            self.log("SUCCESS", f"{user.username}, '{f.filename}' dosyasını okudu")
            messagebox.showinfo("📖 Dosya İçeriği", f"{f.filename}\n\n{f.content}")

        elif action == "w":
            new_text = ctk.CTkInputDialog(
                text="Eklenecek metni girin:",
                title="✍️ Dosya Düzenle"
            ).get_input()

            if new_text is None:
                self.log("INFO", f"{user.username}, '{f.filename}' düzenleme işlemini iptal etti")
                return

            f.content += "\n" + new_text
            f.modified_at = datetime.now()
            self.save_data()
            self.update_info()
            self.update_statistics()
            self.log("SUCCESS", f"{user.username}, '{f.filename}' içeriğini güncelledi")

        elif action == "x":
            f.accessed_at = datetime.now()
            self.save_data(quiet=True)
            self.update_info()

            executed = self.execute_file(f)
            if executed:
                self.log("SUCCESS", f"{user.username}, '{f.filename}' dosyasını çalıştırdı (simülasyon)")
            else:
                self.log("WARNING", f"'{f.filename}' için çalıştırma izni var; ancak dosya türü çalıştırılamıyor")

    def execute_file(self, file):
        filename = file.filename
        content = file.content
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".py":
            messagebox.showinfo(
                "⚡ Python Betiği",
                f"'{filename}' Python betiği olarak çalıştırıldı! (simülasyon)\n\n"
                f"İçerik:\n{content[:300]}{'...' if len(content) > 300 else ''}\n\n"
                "(Not: Güvenlik nedeniyle bu simülatör dosya içeriğini gerçekten "
                "çalıştırmaz, sadece 'x' izninin geçerli olduğunu gösterir.)"
            )
            return True

        if ext in (".sh", ".bash"):
            messagebox.showinfo(
                "⚡ Shell Script",
                f"'{filename}' shell script olarak çalıştırıldı! (simülasyon)\n\n"
                f"İçerik:\n{content[:300]}{'...' if len(content) > 300 else ''}"
            )
            return True

        if ext in (".txt", ".md"):
            messagebox.showinfo(
                "⚡ Metin Dosyası",
                f"'{filename}' bir metin dosyasıdır, doğrudan çalıştırılamaz.\n\n"
                f"İçerik:\n{content[:500]}{'...' if len(content) > 500 else ''}"
            )
            return False

        messagebox.showinfo(
            "⚡ Çalıştırma",
            f"'{filename}' dosyası çalıştırılamıyor.\n"
            f"Dosya türü: {ext if ext else 'belirsiz'}\n\n"
            f"İçerik önizleme:\n{content[:200]}{'...' if len(content) > 200 else ''}"
        )
        return False


if __name__ == "__main__":
    App().mainloop()
