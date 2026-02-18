import sys
import cv2
import numpy as np
import pytesseract
import easyocr
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QWidget, QFileDialog, QLabel, QTextEdit, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class BelgeOkuyucu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Belge Okuyucu")
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Üst kısım - Butonlar
        top_layout = QHBoxLayout()
        self.klasor_sec_btn = QPushButton("Klasör Seç")
        self.tara_btn = QPushButton("TARA")
        self.klasor_yolu_label = QLabel("Seçilen klasör: ")
        
        top_layout.addWidget(self.klasor_sec_btn)
        top_layout.addWidget(self.tara_btn)
        top_layout.addWidget(self.klasor_yolu_label)
        top_layout.addStretch()
        
        # Orta kısım - Görüntü ve metin
        middle_layout = QHBoxLayout()
        
        # Sol taraf - Görüntü gösterimi ve navigasyon butonları
        left_layout = QVBoxLayout()
        
        # Görüntü gösterimi
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.setWidgetResizable(True)
        
        # Navigasyon butonları
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Önceki")
        self.next_btn = QPushButton("Sonraki")
        self.image_counter_label = QLabel("0/0")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_counter_label)
        nav_layout.addWidget(self.next_btn)
        
        left_layout.addWidget(self.image_scroll)
        left_layout.addLayout(nav_layout)
        
        # Sağ taraf - Metin gösterimi
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        middle_layout.addLayout(left_layout, 2)
        middle_layout.addWidget(self.text_edit, 1)
        
        # Layout'ları ana layout'a ekle
        layout.addLayout(top_layout)
        layout.addLayout(middle_layout)
        
        # Buton bağlantıları
        self.klasor_sec_btn.clicked.connect(self.klasor_sec)
        self.tara_btn.clicked.connect(self.tara)
        self.prev_btn.clicked.connect(self.show_previous_image)
        self.next_btn.clicked.connect(self.show_next_image)
        
        # Değişkenler
        self.secilen_klasor = ""
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Görüntü listesi ve mevcut görüntü indeksi
        self.detected_images = []  # [(image_path, text, processed_image), ...]
        self.current_image_index = -1
        
        # Başlangıçta navigasyon butonlarını devre dışı bırak
        self.update_nav_buttons()

    def klasor_sec(self):
        self.secilen_klasor = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        self.klasor_yolu_label.setText(f"Seçilen klasör: {self.secilen_klasor}")

    def detect_id_documents(self, image_path):
        # Görüntüyü oku
        image = cv2.imread(image_path)
        
        # Görüntüyü gri tonlamaya çevir
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Kenar tespiti
        edges = cv2.Canny(gray, 50, 150)
        
        # Konturları bul
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Muhtemel kimlik belgesi alanlarını tespit et
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50000:  # Minimum alan eşiği
                # Dikdörtgen sınırları al
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w)/h
                
                # Kimlik belgelerinin genellikle sahip olduğu en-boy oranı kontrolü
                if 1.3 <= aspect_ratio <= 1.8:
                    # Tespit edilen alanı kes
                    roi = gray[y:y+h, x:x+w]
                    
                    # Tesseract OCR ile metin okuma
                    text = pytesseract.image_to_string(roi, lang='tur')
                    
                    # EasyOCR ile metin okuma
                    reader = easyocr.Reader(['tr'])
                    results = reader.readtext(roi)
                    
                    # Metin sonuçlarını birleştir
                    full_text = "Tesseract OCR sonucu:\n"
                    full_text += text
                    full_text += "\n\nEasyOCR sonucu:\n"
                    for result in results:
                        full_text += f"{result[1]}: {result[2]:.2f}\n"
                    
                    # İşaretlenmiş görüntüyü hazırla
                    cv2.rectangle(image, (x,y), (x+w,y+h), (0,255,0), 2)
                    
                    # Görüntüyü kaydet
                    output_path = os.path.join(self.sonuclar_klasoru, f'tespit_{os.path.basename(image_path)}')
                    cv2.imwrite(output_path, image)
                    
                    # Görüntü ve metin bilgilerini listeye ekle
                    self.detected_images.append((image_path, full_text, image))
                    return True
        return False

    def tara(self):
        if not self.secilen_klasor:
            self.text_edit.setText("Lütfen önce bir klasör seçin!")
            return
            
        # Sonuçlar klasörünü oluştur
        self.sonuclar_klasoru = os.path.join(self.secilen_klasor, "SONUCLAR")
        if not os.path.exists(self.sonuclar_klasoru):
            os.makedirs(self.sonuclar_klasoru)
        
        # Önceki sonuçları temizle
        self.detected_images.clear()
        self.current_image_index = -1
        self.text_edit.clear()
        
        # Görüntüleri işle
        for filename in os.listdir(self.secilen_klasor):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(self.secilen_klasor, filename)
                self.text_edit.append(f"\n--- İşlenen dosya: {filename} ---\n")
                
                if not self.detect_id_documents(image_path):
                    self.text_edit.append("Bu görüntüde belge tespit edilemedi!")
        
        self.text_edit.append(f"\nTarama tamamlandı! {len(self.detected_images)} belge tespit edildi.")
        
        # İlk görüntüyü göster
        if self.detected_images:
            self.current_image_index = 0
            self.show_current_image()
        
        # Navigasyon butonlarını güncelle
        self.update_nav_buttons()

    def show_current_image(self):
        if 0 <= self.current_image_index < len(self.detected_images):
            _, text, image = self.detected_images[self.current_image_index]
            self.show_image(image)
            self.text_edit.setText(text)
            self.image_counter_label.setText(f"{self.current_image_index + 1}/{len(self.detected_images)}")

    def show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
            self.update_nav_buttons()

    def show_next_image(self):
        if self.current_image_index < len(self.detected_images) - 1:
            self.current_image_index += 1
            self.show_current_image()
            self.update_nav_buttons()

    def update_nav_buttons(self):
        self.prev_btn.setEnabled(self.current_image_index > 0)
        self.next_btn.setEnabled(self.current_image_index < len(self.detected_images) - 1)

    def show_image(self, cv_img):
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.image_scroll.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BelgeOkuyucu()
    window.show()
    sys.exit(app.exec_())