from pdf2image import convert_from_path
import cv2
import pytesseract
import numpy as np  # وارد کردن numpy برای تبدیل تصاویر

# مسیر فایل PDF (این را به مسیر فایل PDF خود تغییر دهید)
pdf_path = "dehkhoda1.pdf"

# تبدیل PDF به لیستی از تصاویر در حافظه (هر صفحه یک تصویر)
pages = convert_from_path(pdf_path, dpi=300)

# پردازش هر صفحه از PDF
for i, page in enumerate(pages):
    # تبدیل صفحه PDF به فرمت OpenCV با استفاده از NumPy
    page_image = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
    
    # تبدیل تصویر به مقیاس خاکستری
    gray = cv2.cvtColor(page_image, cv2.COLOR_BGR2GRAY)

    # اعمال thresholding برای بهبود کیفیت متن
    _, binary_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # استخراج متن از تصویر با استفاده از Tesseract
    text = pytesseract.image_to_string(binary_image, lang='fas')

    # ذخیره متن استخراج شده به فایل متنی
    text_output_path = f"extracted_text_page_{i + 1}.txt"
    with open(text_output_path, "w", encoding="utf-8") as file:
        file.write(text)

    print(f"متن استخراج شده از صفحه {i + 1} ذخیره شد به عنوان {text_output_path}")
