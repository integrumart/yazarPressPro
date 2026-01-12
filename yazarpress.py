import sys, requests, json, os, winsound, datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, QTextEdit, 
                             QPushButton, QComboBox, QMessageBox, QTabWidget, QFormLayout, 
                             QHBoxLayout, QListWidget, QFileDialog, QLabel)
from PyQt6.QtGui import QTextCharFormat, QFont, QIcon
from PyQt6.QtCore import Qt

def kaynak_yolu(goreceli_yol):
    """PyInstaller paketlemesi sonrası dosyalara erişmek için yolu düzeltir."""
    try:
        # PyInstaller dosyaları _MEIPASS içine açar
        taban_yol = sys._MEIPASS
    except Exception:
        taban_yol = os.path.abspath(".")
    return os.path.join(taban_yol, goreceli_yol)

class YazarPress(QWidget):
    def __init__(self):
        super().__init__()
        # Kurumsal AppData Klasör Yapısı
        self.appdata_yolu = os.path.join(os.getenv('LOCALAPPDATA'), "YazarPress_Pro")
        os.makedirs(self.appdata_yolu, exist_ok=True)
        self.ayar_f = os.path.join(self.appdata_yolu, "config.json")
        self.arsiv_f = os.path.join(self.appdata_yolu, "storage.json")
        self.secili_gorsel_yolu = ""
        
        # Uygulama İkonu ve Pencere Logosu (favicon.ico kullanılıyor)
        self.icon_yolu = kaynak_yolu("favicon.ico")
        if os.path.exists(self.icon_yolu):
            self.setWindowIcon(QIcon(self.icon_yolu))

        self.init_ui()
        self.apply_corporate_style()
        self.load_settings()
        self.refresh_local_list()

    def apply_corporate_style(self):
        """Uygulamaya modern kurumsal bir görünüm kazandırır."""
        self.setStyleSheet("""
            QWidget { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; color: #333; }
            QTabWidget::pane { border: 1px solid #cfd8dc; background: white; border-radius: 4px; }
            QTabBar::tab { background: #e1e8ed; padding: 12px 25px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: white; border-bottom: 2px solid #007bff; font-weight: bold; color: #007bff; }
            QLineEdit, QTextEdit, QComboBox { border: 1px solid #ced4da; border-radius: 4px; padding: 8px; background: white; }
            QPushButton { background-color: #007bff; color: white; border-radius: 4px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton#action_btn { background-color: #28a745; border: none; }
            QPushButton#action_btn:hover { background-color: #218838; }
            QListWidget { border: 1px solid #dee2e6; border-radius: 4px; background: white; }
        """)

    def init_ui(self):
        self.setWindowTitle('YazarPress Pro - Kurumsal İçerik Paneli')
        self.setGeometry(200, 50, 1000, 850)
        ana_duzen = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # --- SEKME 1: YAZI EDİTÖRÜ ---
        self.t1 = QWidget(); l1 = QVBoxLayout(); f1 = QFormLayout()
        self.e_t = QLineEdit(); self.e_t.setPlaceholderText("İçerik başlığını buraya girin...")
        f1.addRow("Başlık:", self.e_t)
        
        h_kat = QHBoxLayout()
        self.c_tp = QComboBox(); self.c_tp.addItems(["Yazı (Post)", "Sayfa (Page)"])
        self.c_ct = QComboBox(); self.c_ct.addItem("Kategorileri Çekmek İçin Ayarları Kaydedin", 0)
        btn_refresh_cat = QPushButton("🔄"); btn_refresh_cat.setFixedWidth(40)
        btn_refresh_cat.clicked.connect(self.fetch_categories)
        h_kat.addWidget(self.c_tp); h_kat.addWidget(self.c_ct); h_kat.addWidget(btn_refresh_cat)
        f1.addRow("Tür / Kategori:", h_kat)

        self.e_tg = QLineEdit(); self.e_tg.setPlaceholderText("etiket1, etiket2, etiket3")
        f1.addRow("Etiketler:", self.e_tg)

        gorsel_layout = QHBoxLayout()
        self.lbl_gorsel = QLabel("Görsel Seçilmedi")
        btn_gorsel = QPushButton("Kapak Fotoğrafı Seç"); btn_gorsel.clicked.connect(self.gorsel_sec)
        gorsel_layout.addWidget(self.lbl_gorsel); gorsel_layout.addWidget(btn_gorsel)
        f1.addRow("Görsel:", gorsel_layout)

        araclar = QHBoxLayout()
        b_b = QPushButton("B"); b_b.setFixedWidth(35); b_b.clicked.connect(self.set_bold)
        b_i = QPushButton("/"); b_i.setFixedWidth(35); b_i.clicked.connect(self.set_italic)
        self.btn_mode = QPushButton("HTML Görünümü"); self.btn_mode.setCheckable(True)
        self.btn_mode.toggled.connect(self.toggle_editor_mode)
        araclar.addWidget(b_b); araclar.addWidget(b_i); araclar.addStretch(); araclar.addWidget(self.btn_mode)
        f1.addRow("Araçlar:", araclar)

        self.txt = QTextEdit()
        l1.addLayout(f1); l1.addWidget(self.txt)

        btn_box = QHBoxLayout()
        btn_local = QPushButton("💾 Arşive Kaydet"); btn_local.clicked.connect(self.save_local_draft)
        btn_draft = QPushButton("📝 Taslak Gönder"); btn_draft.clicked.connect(lambda: self.send_to_wp("draft"))
        self.btn_pub = QPushButton("🚀 HEMEN YAYINLA"); self.btn_pub.setObjectName("action_btn")
        self.btn_pub.clicked.connect(lambda: self.send_to_wp("publish"))
        
        btn_box.addWidget(btn_local); btn_box.addWidget(btn_draft); btn_box.addWidget(self.btn_pub)
        l1.addLayout(btn_box); self.t1.setLayout(l1)

        # --- SEKME 2: CANLI SİTE ---
        self.t2 = QWidget(); l2 = QVBoxLayout()
        btn_fetch = QPushButton("Sitedeki Son 10 Yazıyı Göster"); btn_fetch.clicked.connect(self.fetch_published_posts)
        self.wp_list = QListWidget(); l2.addWidget(btn_fetch); l2.addWidget(self.wp_list); self.t2.setLayout(l2)

        # --- SEKME 3: YEREL ARŞİV ---
        self.t3 = QWidget(); l3 = QVBoxLayout()
        self.local_list = QListWidget(); l3.addWidget(self.local_list)
        bl = QHBoxLayout(); btn_edit = QPushButton("Düzenle"); btn_edit.clicked.connect(self.load_local_item)
        btn_del = QPushButton("Sil"); btn_del.clicked.connect(self.delete_local_item)
        bl.addWidget(btn_edit); bl.addWidget(btn_del); l3.addLayout(bl); self.t3.setLayout(l3)

        # --- SEKME 4: AYARLAR ---
        self.t4 = QWidget(); f4 = QFormLayout()
        self.u = QLineEdit(); self.u.setPlaceholderText("https://siteniz.com")
        self.un = QLineEdit(); self.un.setPlaceholderText("Admin kullanıcı adınız")
        self.pw = QLineEdit(); self.pw.setEchoMode(QLineEdit.EchoMode.Password); self.pw.setPlaceholderText("Uygulama Şifresi")
        btn_save_cfg = QPushButton("AYARLARI KAYDET VE BAĞLAN"); btn_save_cfg.clicked.connect(self.save_settings)
        f4.addRow("Site URL:", self.u); f4.addRow("Kullanıcı Adı:", self.un); f4.addRow("Uygulama Şifresi:", self.pw); f4.addRow(btn_save_cfg)
        self.t4.setLayout(f4)

        self.tabs.addTab(self.t1, "Yazı Yaz"); self.tabs.addTab(self.t2, "Canlı Site"); self.tabs.addTab(self.t3, "Arşiv"); self.tabs.addTab(self.t4, "Ayarlar")
        ana_duzen.addWidget(self.tabs); self.setLayout(ana_duzen)

    # --- ÖZELLİKLER VE FONKSİYONLAR ---
    def fetch_categories(self):
        url = f"{self.u.text().strip().rstrip('/')}/wp-json/wp/v2/categories?per_page=100"
        try:
            r = requests.get(url, auth=(self.un.text(), self.pw.text()), timeout=10)
            if r.status_code == 200:
                self.c_ct.clear()
                for cat in r.json(): self.c_ct.addItem(cat['name'], cat['id'])
        except: self.c_ct.setItemText(0, "Bağlantı Kurulamadı!")

    def gorsel_sec(self):
        path, _ = QFileDialog.getOpenFileName(self, "Görsel Seç", "", "Resim Dosyaları (*.jpg *.png *.jpeg *.ico)")
        if path: self.secili_gorsel_yolu = path; self.lbl_gorsel.setText(os.path.basename(path))

    def upload_media(self):
        if not self.secili_gorsel_yolu: return None
        url = f"{self.u.text().strip().rstrip('/')}/wp-json/wp/v2/media"
        headers = {'Content-Disposition': f'attachment; filename={os.path.basename(self.secili_gorsel_yolu)}'}
        try:
            with open(self.secili_gorsel_yolu, 'rb') as f:
                r = requests.post(url, data=f, headers=headers, auth=(self.un.text(), self.pw.text()), timeout=30)
                return r.json().get('id') if r.status_code == 201 else None
        except: return None

    def send_to_wp(self, status):
        if not self.e_t.text(): QMessageBox.critical(self, "Hata", "Lütfen bir başlık girin!"); return
        media_id = self.upload_media()
        url = self.u.text().strip().rstrip("/")
        tur = "posts" if self.c_tp.currentIndex() == 0 else "pages"
        payload = {
            "title": self.e_t.text(),
            "content": self.txt.toHtml() if not self.btn_mode.isChecked() else self.txt.toPlainText(),
            "status": status,
            "featured_media": media_id if media_id else 0,
            "tags": [t.strip() for t in self.e_tg.text().split(",") if t.strip()]
        }
        if tur == "posts": payload["categories"] = [self.c_ct.currentData()]
        try:
            r = requests.post(f"{url}/wp-json/wp/v2/{tur}", json=payload, auth=(self.un.text(), self.pw.text()), timeout=30)
            if r.status_code in [200, 201]:
                QMessageBox.information(self, "Başarılı", f"İçerik {status} olarak gönderildi!")
                winsound.MessageBeep(winsound.MB_OK)
            else: QMessageBox.warning(self, "Hata", f"Sunucu Hatası: {r.status_code}")
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def save_local_draft(self):
        data = {"title": self.e_t.text(), "content": self.txt.toHtml(), "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
        arsiv = []
        if os.path.exists(self.arsiv_f):
            with open(self.arsiv_f, "r", encoding="utf-8") as f: arsiv = json.load(f)
        arsiv.append(data)
        with open(self.arsiv_f, "w", encoding="utf-8") as f: json.dump(arsiv, f, ensure_ascii=False, indent=4)
        self.refresh_local_list()

    def refresh_local_list(self):
        self.local_list.clear()
        if os.path.exists(self.arsiv_f):
            with open(self.arsiv_f, "r", encoding="utf-8") as f:
                for item in json.load(f): self.local_list.addItem(f"[{item['date']}] {item['title']}")

    def load_local_item(self):
        idx = self.local_list.currentRow()
        if idx != -1:
            with open(self.arsiv_f, "r", encoding="utf-8") as f:
                data = json.load(f)[idx]
                self.e_t.setText(data['title']); self.txt.setHtml(data['content']); self.tabs.setCurrentIndex(0)

    def delete_local_item(self):
        idx = self.local_list.currentRow()
        if idx != -1:
            with open(self.arsiv_f, "r", encoding="utf-8") as f: arsiv = json.load(f)
            arsiv.pop(idx)
            with open(self.arsiv_f, "w", encoding="utf-8") as f: json.dump(arsiv, f, ensure_ascii=False, indent=4)
            self.refresh_local_list()

    def fetch_published_posts(self):
        self.wp_list.clear()
        try:
            r = requests.get(f"{self.u.text().strip()}/wp-json/wp/v2/posts?per_page=10", auth=(self.un.text(), self.pw.text()))
            if r.status_code == 200:
                for post in r.json(): self.wp_list.addItem(f"• {post['title']['rendered']}")
        except: self.wp_list.addItem("Bağlantı hatası!")

    def toggle_editor_mode(self, checked):
        if checked: self.txt.setPlainText(self.txt.toHtml())
        else: self.txt.setHtml(self.txt.toPlainText())

    def set_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.txt.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        self.txt.mergeCurrentCharFormat(fmt)

    def set_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.txt.fontItalic())
        self.txt.mergeCurrentCharFormat(fmt)

    def save_settings(self):
        config = {"u": self.u.text(), "un": self.un.text(), "pw": self.pw.text()}
        with open(self.ayar_f, "w", encoding="utf-8") as f: json.dump(config, f, ensure_ascii=False, indent=4)
        self.fetch_categories()
        QMessageBox.information(self, "Sistem", "Bağlantı ayarları güncellendi.")

    def load_settings(self):
        if os.path.exists(self.ayar_f):
            with open(self.ayar_f, "r", encoding="utf-8") as f:
                c = json.load(f)
                self.u.setText(c.get("u", "")); self.un.setText(c.get("un", "")); self.pw.setText(c.get("pw", ""))
            self.fetch_categories()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pencere = YazarPress()
    pencere.show()
    sys.exit(app.exec())