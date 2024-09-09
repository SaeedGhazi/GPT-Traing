import pytesseract
from PIL import Image
import re

# مسیر فایل Tesseract خود را تنظیم کنید
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # برای لینوکس

def extract_text_from_image(image_path):
    """
    تبدیل تصویر به متن با استفاده از Tesseract
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='fas')  # OCR با زبان فارسی
    return text

def process_text(text):
    """
    پردازش متن برای استخراج کلمات، آواها، ریشه‌ها، نوع کلمه و معنی
    """
    # الگوی Regex برای استخراج بخش‌های مختلف
    pattern = re.compile(r'(?P<word>\S+):?\s+(?P<phonetic>\[.*?\])?\s*(?P<root>\(.*?\))?\s*(?P<definition>.*)')

    results = []
    for match in re.finditer(pattern, text):
        word = match.group('word')
        phonetic = match.group('phonetic') if match.group('phonetic') else ''
        root = match.group('root') if match.group('root') else ''
        definition = match.group('definition') if match.group('definition') else ''

        # حذف کروشه‌ها و پرانتزها
        phonetic = phonetic.replace('[', '').replace(']', '')
        root = root.replace('(', '').replace(')', '')

        results.append({
            'word': word,
            'phonetic': phonetic,
            'root': root,
            'definition': definition
        })
    
    return results

def main(image_path):
    # مرحله 1: تبدیل تصویر به متن
    text = extract_text_from_image(image_path)

    # مرحله 2: پردازش متن برای استخراج اطلاعات
    processed_data = process_text(text)

    # نمایش اطلاعات استخراج‌شده
    for data in processed_data:
        print(f"کلمه: {data['word']}")
        print(f"آوا: {data['phonetic']}")
        print(f"ریشه: {data['root']}")
        print(f"معنی: {data['definition']}")
        print('-------------------')

# مسیر فایل تصویر خود را وارد کنید
image_path = '/home/ssq/Downloads/poem_epub/dic.image.png'

main(image_path)
