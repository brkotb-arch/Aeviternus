# core/vision.py
"""
Зрение Дипа. Позволяет анализировать изображения и PDF-файлы.
"""

import os
import base64
import tempfile
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import io
import json

# Настройка пути к Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def image_to_text(image_data: bytes) -> str:
    """
    Распознаёт текст с изображения (скриншота).
    Принимает bytes изображения, возвращает строку текста.
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        # Распознаём текст на русском
        text = pytesseract.image_to_string(image, lang="rus+eng")
        return text.strip() if text.strip() else "(текст не распознан)"
    except Exception as e:
        return f"(ошибка распознавания: {e})"

def pdf_to_text(pdf_data: bytes) -> str:
    """
    Извлекает текст из PDF-файла.
    Принимает bytes PDF, возвращает строку текста.
    """
    try:
        text_parts = []
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        for page in pdf_document:
            text_parts.append(page.get_text())
        pdf_document.close()
        full_text = "\n".join(text_parts)
        return full_text.strip() if full_text.strip() else "(текст не найден)"
    except Exception as e:
        return f"(ошибка чтения PDF: {e})"

def describe_image(image_data: bytes) -> str:
    """
    Описывает изображение: текст + базовая информация.
    Для полноценного описания картинок нужна мультимодальная модель,
    но для скриншотов и документов OCR достаточно.
    """
    # Сначала пробуем распознать текст
    text = image_to_text(image_data)
    
    # Базовая информация об изображении
    try:
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        info = f"[Изображение: {width}x{height}]"
    except:
        info = "[Изображение]"
    
    if text:
        return f"{info}\nРаспознанный текст:\n{text}"
    else:
        return f"{info}\n(текст не обнаружен)"