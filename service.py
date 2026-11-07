import time
from datetime import datetime

import core

core.log("service started")

# خدمة خلفية: تفحص كل نصف ساعة، وترسل الإشعارات بعد الساعة التي اختارها المستخدم
while True:
    try:
        if datetime.now().hour >= core.notify_hour():
            errors = core.check_and_notify()
            if errors:
                core.log(f"service errors: {errors}")
    except Exception as e:
        core.log(f"service crash: {e}")
    time.sleep(1800)
    
