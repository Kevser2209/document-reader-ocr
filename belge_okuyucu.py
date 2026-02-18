import cv2
import numpy as np
import pytesseract
import easyocr
import os

# Tesseract yolunu belirtin
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def detect_id_documents(image_path):
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
                
                # EasyOCR ile metin okuma (daha iyi sonuçlar için)
                reader = easyocr.Reader(['tr'])
                results = reader.readtext(roi)
                
                print("Tespit edilen metin (Tesseract):")
                print(text)
                print("\nTespit edilen metin (EasyOCR):")
                for result in results:
                    print(f"{result[1]}: {result[2]:.2f}")
                
                # İşlenmiş görüntüyü kaydet
                output_path = os.path.join('sonuclar', f'tespit_{os.path.basename(image_path)}')
                cv2.rectangle(image, (x,y), (x+w,y+h), (0,255,0), 2)
                cv2.imwrite(output_path, image)
                print(f"\nİşlenmiş görüntü kaydedildi: {output_path}")

# Klasördeki tüm görüntüleri işle
def process_folder(folder_path):
    # Sonuçlar klasörünü oluştur
    if not os.path.exists('sonuclar'):
        os.makedirs('sonuclar')
        
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder_path, filename)
            print(f"\nİşlenen dosya: {filename}")
            detect_id_documents(image_path)

# Kullanım örneği
folder_path = "belgeler_klasoru"  # Kendi klasör yolunuzu buraya yazın
process_folder(folder_path)