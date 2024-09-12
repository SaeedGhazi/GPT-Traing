import fitz  # PyMuPDF

# مسیر فایل PDF
pdf_path = "dehkhoda1.pdf"

# باز کردن فایل PDF
pdf_document = fitz.open(pdf_path)

# بررسی صفحات و استخراج DPI هر صفحه
for page_num in range(len(pdf_document)):
    page = pdf_document.load_page(page_num)  # بارگذاری صفحه
    zoom = 1  # بدون تغییر زوم
    mat = fitz.Matrix(zoom, zoom)
    
    # استخراج ابعاد صفحه در پیکسل
    pix = page.get_pixmap(matrix=mat)
    width_pix, height_pix = pix.width, pix.height

    # ابعاد صفحه در اینچ
    width_inch, height_inch = page.rect.width / 72, page.rect.height / 72  # 1 اینچ = 72 پوینت

    # محاسبه DPI
    dpi_width = width_pix / width_inch
    dpi_height = height_pix / height_inch

    print(f"صفحه {page_num + 1}: DPI عرض = {dpi_width}, DPI ارتفاع = {dpi_height}")

pdf_document.close()
