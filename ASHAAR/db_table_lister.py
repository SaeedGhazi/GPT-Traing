import sqlite3

# مسیر فایل پایگاه داده
db_path = "db_loqat.db"

# اتصال به پایگاه داده
conn = sqlite3.connect(db_path)

# ایجاد cursor برای اجرای کوئری‌ها
cursor = conn.cursor()

# کوئری برای نمایش کلیه جداول موجود در پایگاه داده
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# نمایش جداول موجود
print("جداول پایگاه داده:")
for table in tables:
    print(table[0])

# بستن اتصال به پایگاه داده
conn.close()
