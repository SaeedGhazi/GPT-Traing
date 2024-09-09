import os
import json
from ebooklib import epub
from bs4 import BeautifulSoup
import ebooklib

def extract_text_from_epub(epub_path):
    """
    استخراج متن از فایل EPUB و ترکیب دو خط متوالی به عنوان یک بیت
    """
    book = epub.read_epub(epub_path)
    all_poems = []
    
    # مرور بخش‌های کتاب برای یافتن شعرها
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:  # تغییر برای استفاده از ebooklib.ITEM_DOCUMENT
            # استفاده از BeautifulSoup برای استخراج متن از هر بخش HTML
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            # تقسیم هر بخش به خطوط
            lines = [line.strip() for line in soup.get_text().split('\n') if line.strip()]
            # ترکیب هر دو خط به عنوان یک بیت
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    # ترکیب دو خط متوالی به عنوان یک بیت
                    verse = lines[i] + ' / ' + lines[i + 1]
                    all_poems.append(verse)
    
    return all_poems

def process_folder(epub_folder, output_file):
    """
    پردازش تمامی فایل‌های EPUB در یک پوشه و ذخیره آن‌ها در قالب JSON
    """
    all_books_data = {}
    
    # مرور همه فایل‌های EPUB در پوشه
    for file_name in os.listdir(epub_folder):
        if file_name.endswith(".epub"):
            file_path = os.path.join(epub_folder, file_name)
            print(f"در حال پردازش: {file_name}")
            book_title = file_name.replace('.epub', '')  # عنوان کتاب بر اساس نام فایل
            poems = extract_text_from_epub(file_path)
            
            # اضافه کردن کتاب به داده‌ها
            all_books_data[book_title] = []
            for i, poem in enumerate(poems, start=1):
                # ساختار هر شعر شامل اندیس و متن
                poem_data = {
                    "poem_index": i,
                    "verse": poem
                }
                all_books_data[book_title].append(poem_data)
    
    # ذخیره در قالب فایل JSON
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(all_books_data, json_file, ensure_ascii=False, indent=4)

    print(f"پردازش تکمیل شد! داده‌ها در فایل {output_file} ذخیره شدند.")

# استفاده از تابع برای پردازش یک پوشه
epub_folder = '.'  # مسیر پوشه‌ای که فایل‌های EPUB در آن قرار دارند
output_file = 'poems_output.json'  # نام فایل خروجی JSON

process_folder(epub_folder, output_file)
