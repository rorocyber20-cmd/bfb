import time
from datetime import datetime

from core import check_and_notify

# خدمة خلفية: تفحص كل ساعة، وترسل الإشعارات بعد الساعة 9 صباحًا فقط
while True:
    try:
        if datetime.now().hour >= 9:
            check_and_notify()
    except Exception as e:
        print(f"[service error]: {e}")
    time.sleep(3600)
