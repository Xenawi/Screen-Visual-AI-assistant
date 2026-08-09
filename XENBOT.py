import tkinter as tk
import pyautogui
from io import BytesIO
import base64
import customtkinter as ctk
import google.generativeai as genai
import time
import threading
import os
import json
import shutil
import sys
from PyQt5.QtWidgets import QApplication, QRubberBand, QWidget
from PyQt5.QtCore import QRect, QPoint, QSize
from PIL import Image, ImageEnhance
import tempfile
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor


# ===============================================================
# API CONFIG
# ===============================================================

GEMINI_API_KEYS = [
    "API-Key1",
    "API-Key2",
    "API-Key3",
    "API-Key4",
]

MODEL_NAME = "gemini-2.5-flash"  # Vision + text model


# ===============================================================
# SCREENSHOT TOOL
# ===============================================================

class ScreenshotTool(QWidget):
    def __init__(self, save_path):
        super().__init__()
        self.save_path = save_path

        # Selection start/end
        self.start = QPoint()
        self.end = QPoint()

        # Transparent overlay window (very lightweight)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Dim background (lightweight)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

        # Draw selection rectangle
        if not self.start.isNull() and not self.end.isNull():
            pen = QPen(Qt.green, 2)
            painter.setPen(pen)
            rect = QRect(self.start, self.end)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.start = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        self.update()

        # Normalize rectangle values
        rect = QRect(self.start, self.end).normalized()

        QApplication.processEvents()

        # Capture screen (super-efficient)
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())

        # Save image
        screenshot.save(self.save_path, "png")

        # Close tool immediately
        self.close()

# ===============================================================
# MAIN APP
# ===============================================================

class VisionApp:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.api_index = 0
        self.configure_api()

        self.root = ctk.CTk()
        self.root.title("SEB Protector")
        self.root.geometry("250x650+0+0")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # API switch buttons
        self.api_frame = ctk.CTkFrame(self.root, fg_color="black")
        self.api_frame.pack(pady=(5, 15))

        for i in range(len(GEMINI_API_KEYS)):
            btn = ctk.CTkButton(
                self.api_frame, text=f" --{i+1} ",
                command=lambda i=i: self.switch_key(i),
                fg_color="white", text_color="black", width=90
            )
            btn.grid(row=i, column=0)

        self.prompt = ctk.CTkEntry(self.root, placeholder_text="Enter prompt here")
        self.prompt.pack(padx=5, pady=5)

        self.send_prompt = ctk.CTkButton(
            self.root, text="Send Prompt",
            command=lambda: self.start_thread(True),
            fg_color="white", text_color="black"
        )
        self.send_prompt.pack(pady=5)

        self.textbox = ctk.CTkTextbox(
            self.root, width=780, height=320,
            font=("Consolas", 14), fg_color="white", text_color="black"
        )
        self.textbox.pack(pady=10)

        self.capture_button = ctk.CTkButton(
            self.root, text=" Troubleshoot ",
            command=lambda: self.start_thread(False),
            fg_color="white", text_color="black"
        )
        self.capture_button.pack(pady=3)

        self.clear_button = ctk.CTkButton(
            self.root, text=" Clear ", command=self.clear_history,
            fg_color="white", text_color="black"
        )
        self.clear_button.pack()

    # ===============================================================
    # API CONFIG
    # ===============================================================

    def configure_api(self):
        genai.configure(api_key=GEMINI_API_KEYS[self.api_index])

        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=(
                "You are an expert AI assistant. "
                "Always analyze screenshots carefully. "
                "When errors appear, explain the cause and provide the fix. "
                "When code appears, provide corrected code. "
                "Be clear, structured, and concise."
            ),
            generation_config={
                "temperature": 0.25,
                "top_p": 0.95,
                "max_output_tokens": 2048
            }
        )

    def switch_key(self, i):
        self.api_index = i
        self.configure_api()
        self._insert_text(f"\n[INFO] Switched to API key {i+1}\n")

    def rotate_key(self):
        self.api_index = (self.api_index + 1) % len(GEMINI_API_KEYS)
        self.configure_api()
        self._insert_text(f"\n[INFO] Rotated to backup API key {self.api_index+1}\n")

    # ===============================================================
    # SCREENSHOT HANDLING
    # ===============================================================

    def take_screenshot(self):
        # Ensure Qt app instance exists
        app = QApplication.instance() or QApplication([])

        # Create temporary file path
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = tmp.name
        tmp.close()

        # Launch screenshot tool (non-blocking)
        tool = ScreenshotTool(save_path=tmp_path)

        # Run Qt event loop until screenshot is saved
        app.processEvents()

        # Wait until screenshot file is written
        while not (os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 10):
            app.processEvents()

        # Load and enhance the image
        img = Image.open(tmp_path)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Sharpness(img).enhance(1.3)

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        # Cleanup
        img.close()
        os.remove(tmp_path)

        return image_bytes

    # ===============================================================
    # GEMINI REQUEST THREAD
    # ===============================================================

    def start_thread(self, text_only):
        t = threading.Thread(target=self.ask_gemini, args=(text_only,))
        t.daemon = True
        t.start()

    def ask_gemini(self, text_only=False):
        try:
            user_prompt = self.prompt.get().strip()
            parts = [{"text": user_prompt}]

            if not text_only:
                image_bytes = self.take_screenshot()
                if not image_bytes:
                    self._insert_text("\n[INFO] No screenshot was captured.\n")
                    return
                parts.append({"mime_type": "image/png", "data": image_bytes})

            # Try up to 3 attempts (with key rotation)
            for attempt in range(3):
                try:
                    response = self.model.generate_content(parts)
                    answer = response.text

                    if answer:
                        self._insert_text(f"\nGemini Answer:\n{answer}\n\n")
                        return
                except Exception as e:
                    self._insert_text(f"\n[ERROR] {e}\n")
                    self.rotate_key()
                    time.sleep(1)

            self._insert_text("\n[ERROR] All API keys failed.\n")

        except Exception as ex:
            self._insert_text(f"\n[ERROR] Fatal: {ex}\n")

    # ===============================================================
    # UTILITIES
    # ===============================================================

    def _insert_text(self, text):
        self.root.after(0, lambda: self._safe_insert(text))

    def _safe_insert(self, text):
        self.textbox.insert(tk.END, text)
        self.textbox.see(tk.END)

    def clear_history(self):
        self.textbox.delete("1.0", tk.END)

    def run(self):
        self.root.mainloop()

    def on_closing(self):
        self.root.destroy()
        sys.exit(0)


# ===============================================================
# RUN APP
# ===============================================================

if __name__ == "__main__":
    app = VisionApp()
    app.run()
