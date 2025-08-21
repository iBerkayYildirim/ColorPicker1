#!/usr/bin/env python3
"""
Windows Renk Seçici - Optimize Edilmiş
Bu versiyon Windows'ta mükemmel çalışır
"""

import sys
import platform
import pyautogui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QHBoxLayout, QSystemTrayIcon, 
                             QMenu, QAction, QFrame, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QClipboard
import time

class ColorCaptureThread(QThread):
    """Renk yakalama thread'i"""
    color_updated = pyqtSignal(tuple, tuple, str)  # RGB, pozisyon, hex
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def run(self):
        while self.running:
            try:
                # Mouse pozisyonunu al
                x, y = pyautogui.position()
                
                # Mouse pozisyonundaki rengi yakala
                pixel_color = pyautogui.pixel(x, y)
                
                # Hex kodunu hesapla
                hex_color = '#{:02x}{:02x}{:02x}'.format(*pixel_color)
                
                # Sinyal gönder
                self.color_updated.emit(pixel_color, (x, y), hex_color)
                
                # 50ms bekle (20 FPS)
                time.sleep(0.05)
                
            except Exception as e:
                self.error_occurred.emit(str(e))
                time.sleep(0.1)
    
    def stop(self):
        self.running = False

class WindowsColorPicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupColorCapture()
        self.setupSystemTray()
        
    def initUI(self):
        # Ana pencere ayarları
        self.setWindowTitle('🎨 Windows Renk Seçici v2.0')
        self.setFixedSize(280, 220)
        
        # Pencere konumu (sağ üst köşe)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)
        
        # Pencere özellikleri
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # Merkezi widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Başlık
        title_label = QLabel('🎨 Windows Renk Seçici')
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 5px;")
        main_layout.addWidget(title_label)
        
        # Renk önizleme frame
        color_frame = QFrame()
        color_frame.setFrameStyle(QFrame.Box)
        color_frame.setStyleSheet("QFrame { border: 2px solid #34495e; border-radius: 5px; }")
        color_layout = QVBoxLayout()
        color_frame.setLayout(color_layout)
        
        # Renk önizleme etiketi
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(120, 60)
        self.color_preview.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 3px;")
        self.color_preview.setAlignment(Qt.AlignCenter)
        color_layout.addWidget(self.color_preview)
        
        main_layout.addWidget(color_frame)
        
        # Bilgi etiketleri
        self.hex_label = QLabel('HEX: #000000')
        self.hex_label.setFont(QFont('Consolas', 12, QFont.Bold))
        self.hex_label.setAlignment(Qt.AlignCenter)
        self.hex_label.setStyleSheet("background-color: #ecf0f1; padding: 5px; border-radius: 3px;")
        main_layout.addWidget(self.hex_label)
        
        self.rgb_label = QLabel('RGB: (0, 0, 0)')
        self.rgb_label.setFont(QFont('Consolas', 10))
        self.rgb_label.setAlignment(Qt.AlignCenter)
        self.rgb_label.setStyleSheet("background-color: #ecf0f1; padding: 3px; border-radius: 3px;")
        main_layout.addWidget(self.rgb_label)
        
        self.pos_label = QLabel('Pozisyon: (0, 0)')
        self.pos_label.setFont(QFont('Arial', 9))
        self.pos_label.setAlignment(Qt.AlignCenter)
        self.pos_label.setStyleSheet("color: #7f8c8d;")
        main_layout.addWidget(self.pos_label)
        
        # Buton layout
        button_layout = QHBoxLayout()
        
        # Kopyala butonu
        self.copy_btn = QPushButton('📋 Kopyala')
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.copy_btn.clicked.connect(self.copyColor)
        button_layout.addWidget(self.copy_btn)
        
        # Kapat butonu
        close_btn = QPushButton('❌ Kapat')
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        close_btn.clicked.connect(self.closeApp)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Mouse olayları
        self.color_preview.mouseDoubleClickEvent = self.copyColor
        self.installEventFilter(self)
        
    def setupColorCapture(self):
        """Renk yakalama thread'ini başlat"""
        self.color_thread = ColorCaptureThread()
        self.color_thread.color_updated.connect(self.updateColor)
        self.color_thread.error_occurred.connect(self.handleError)
        self.color_thread.start()
        
    def setupSystemTray(self):
        """System tray icon'u oluştur"""
        try:
            # Basit bir icon oluştur
            icon = QIcon()
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(52, 152, 219))
            icon.addPixmap(pixmap)
            
            self.tray_icon = QSystemTrayIcon(icon, self)
            self.tray_icon.setToolTip('Windows Renk Seçici')
            
            # Tray menüsü
            tray_menu = QMenu()
            show_action = QAction("Göster", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("Çıkış", self)
            quit_action.triggered.connect(self.closeApp)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
        except Exception as e:
            print(f"System tray oluşturulamadı: {e}")
        
    def updateColor(self, rgb_color, position, hex_color):
        """Renk bilgilerini güncelle"""
        try:
            # Pozisyonu güncelle
            self.pos_label.setText(f'Pozisyon: ({position[0]}, {position[1]})')
            
            # RGB değerlerini güncelle
            self.rgb_label.setText(f'RGB: {rgb_color}')
            
            # Hex kodunu güncelle
            self.hex_label.setText(f'HEX: {hex_color}')
            
            # Renk önizlemesini güncelle
            self.updateColorPreview(rgb_color)
            
        except Exception as e:
            print(f"Güncelleme hatası: {e}")
            
    def updateColorPreview(self, rgb_color):
        """Renk önizleme pixmap'ini güncelle"""
        try:
            pixmap = QPixmap(120, 60)
            painter = QPainter(pixmap)
            
            # Arka plan rengini ayarla
            color = QColor(*rgb_color)
            painter.fillRect(0, 0, 120, 60, color)
            
            # Renk değerlerini üzerine yaz
            painter.setPen(QColor(255, 255, 255) if color.lightness() < 128 else QColor(0, 0, 0))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, f'{rgb_color[0]},{rgb_color[1]},{rgb_color[2]}')
            
            painter.end()
            self.color_preview.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Renk önizleme hatası: {e}")
            
    def copyColor(self):
        """Renk kodunu panoya kopyala"""
        try:
            clipboard = QApplication.clipboard()
            hex_text = self.hex_label.text().split(': ')[1]
            clipboard.setText(hex_text)
            
            # Kopyalandı mesajı göster
            self.copy_btn.setText('✅ Kopyalandı!')
            QTimer.singleShot(1000, lambda: self.copy_btn.setText('📋 Kopyala'))
            
            # Başarı mesajı
            QMessageBox.information(self, "Başarılı", f"Renk kodu kopyalandı: {hex_text}")
            
        except Exception as e:
            print(f"Kopyalama hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Renk kodu kopyalanamadı: {e}")
            
    def handleError(self, error_msg):
        """Hata mesajlarını işle"""
        print(f"Renk yakalama hatası: {error_msg}")
        
    def closeApp(self):
        """Uygulamayı kapat"""
        try:
            if hasattr(self, 'color_thread'):
                self.color_thread.stop()
                self.color_thread.wait(1000)
            
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
                
            QApplication.quit()
            
        except Exception as e:
            print(f"Kapatma hatası: {e}")
            QApplication.quit()
            
    def eventFilter(self, obj, event):
        """Global olayları yakala"""
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.closeApp()
                return True
        return super().eventFilter(obj, event)
        
    def closeEvent(self, event):
        """Pencere kapatıldığında"""
        self.closeApp()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Windows stil ayarla
    app.setStyle('Fusion')
    
    # Uygulama bilgileri
    app.setApplicationName('Windows Renk Seçici')
    app.setApplicationVersion('2.0')
    app.setOrganizationName('ColorPicker')
    
    # Ana pencereyi oluştur ve göster
    window = WindowsColorPicker()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
