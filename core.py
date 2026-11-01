import json
import os
from datetime import date, datetime


def data_dir():
    """مجلد بيانات التطبيق: على أندرويد مجلد خاص يبقى بعد التحديثات."""
    try:
        from android.storage import app_storage_path
        return app_storage_path()
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))


DATA_FILE = os.path.join(data_dir(), 'birthdays.json')
NOTIFIED_FILE = os.path.join(data_dir(), 'notified.json')


def _read(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)
        f.flush()
        os.fsync(f.fileno())


def load_birthdays():
    data = _read(DATA_FILE, [])
    if not isinstance(data, list):
        return []
    return [
        {'name': b.get('name', ''), 'date': b.get('date', '')}
        for b in data
        if isinstance(b, dict) and b.get('name') and b.get('date')
    ]


def save_birthdays(items):
    _write(DATA_FILE, items)


def _safe_replace_year(d, year):
    try:
        return d.replace(year=year)
    except ValueError:  # 29 فبراير في سنة غير كبيسة
        return date(year, 3, 1)


def days_until(date_str, today=None):
    """عدد الأيام المتبقية لعيد الميلاد القادم (0 = اليوم)."""
    today = today or date.today()
    born = datetime.strptime(date_str, "%Y-%m-%d").date()
    nxt = _safe_replace_year(born, today.year)
    if nxt < today:
        nxt = _safe_replace_year(born, today.year + 1)
    return (nxt - today).days


def check_and_notify():
    """يرسل إشعار قبل أسبوع وقبل يوم، مرة واحدة فقط لكل موعد."""
    from plyer import notification

    today_str = date.today().isoformat()
    notified = _read(NOTIFIED_FILE, {})
    changed = False

    for item in load_birthdays():
        try:
            d = days_until(item['date'])
        except Exception:
            continue

        if d not in (7, 1):
            continue

        key = f"{item['name']}|{item['date']}|{d}"
        if notified.get(key) == today_str:
            continue

        if d == 7:
            msg = f"باقي أسبوع واحد على عيد ميلاد: {item['name']}!"
        else:
            msg = f"باقي يوم واحد فقط على عيد ميلاد: {item['name']}!"

        try:
            notification.notify(title="تنبيه عيد ميلاد 🎂", message=msg, timeout=10)
            notified[key] = today_str
            changed = True
        except Exception as e:
            print(f"[خطأ إشعار]: {e}")

    if changed:
        try:
            _write(NOTIFIED_FILE, notified)
        except Exception as e:
            print(f"[خطأ حفظ]: {e}")
