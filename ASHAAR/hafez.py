from ebooklib import epub
from bs4 import BeautifulSoup
import ebooklib

def read_epub(epub_path):
    # باز کردن فایل EPUB
    book = epub.read_epub(epub_path)
    
    # مرور تمام بخش‌های کتاب
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:  # استفاده از ebooklib.ITEM_DOCUMENT به جای epub.ITEM_DOCUMENT
            # استفاده از BeautifulSoup برای استخراج متن از HTML
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            text = soup.get_text()
            print(text[:500])  # نمایش 500 کاراکتر اول برای بررسی

# مسیر فایل EPUB خود را وارد کنید
epub_path = 'hafez.epub'

read_epub(epub_path)
