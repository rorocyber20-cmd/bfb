import time
from datetime import datetime

import core

core.log("service started")

# خدمة خلفية: تفحص كل ساعة، وترسل الإشعارات بعد الساعة 9 صباحًا فقط
while True:
    try:
        if datetime.now().hour >= 9:
            errors = core.check_and_notify()
            if errors:
                core.log(f"service errors: {errors}")
    except Exception as e:
        core.log(f"service crash: {e}")
    time.sleep(3600)
