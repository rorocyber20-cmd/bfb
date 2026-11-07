import os
import traceback

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.stencilview import StencilView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import platform
from datetime import date, datetime

IMPORT_ERROR = ''
try:
    import core
except Exception:
    core = None
    IMPORT_ERROR = traceback.format_exc()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(BASE_DIR, 'Cairo-Regular.ttf')

FONT_NAME = 'Roboto'
FONT_ERROR = ''
try:
    if os.path.exists(FONT_FILE):
        LabelBase.register(name='Cairo', fn_regular=FONT_FILE)
        FONT_NAME = 'Cairo'
except Exception:
    FONT_ERROR = traceback.format_exc()


def error_screen(text):
    """شاشة تعرض الخطأ بدل إغلاق التطبيق (للتشخيص)."""
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    label = Label(
        text="BFB Reminder - startup error\n\n" + text,
        size_hint_y=None,
        halign='left',
        valign='top',
        font_size='12sp',
        color=(1, 1, 1, 1),
    )
    label.bind(width=lambda inst, w: setattr(inst, 'text_size', (w - 20, None)))
    label.bind(texture_size=lambda inst, s: setattr(inst, 'height', s[1] + 20))
    sv = ScrollView()
    sv.add_widget(label)
    return sv

# تشكيل الحروف العربية وترتيبها (إن توفرت المكتبتان)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    # خط Cairo المرفق ينقصه الشكل المنفصل (isolated) للحروف، فنستعمل الحرف الأصلي بدله
    try:
        _reshape = arabic_reshaper.ArabicReshaper(
            configuration={'use_unshaped_instead_of_isolated': True}).reshape
    except Exception:
        _reshape = arabic_reshaper.reshape

    def fix_arabic(text):
        try:
            return get_display(_reshape(text))
        except Exception:
            return text
except Exception:
    def fix_arabic(text):
        return text


THEMES = {
    'light': {
        'bg': [0.94, 0.95, 0.97, 1],
        'card': [1, 1, 1, 1],
        'text': [0.2, 0.2, 0.2, 1],
        'muted': [0.5, 0.5, 0.55, 1],
    },
    'dark': {
        'bg': [0.08, 0.09, 0.11, 1],
        'card': [0.14, 0.15, 0.18, 1],
        'text': [0.92, 0.92, 0.95, 1],
        'muted': [0.55, 0.57, 0.62, 1],
    },
}

ACCENTS = {
    'blue': [0.10, 0.50, 0.80, 1],
    'green': [0.18, 0.62, 0.35, 1],
    'purple': [0.55, 0.35, 0.80, 1],
    'orange': [0.93, 0.55, 0.15, 1],
    'red': [0.85, 0.25, 0.30, 1],
    'teal': [0.10, 0.60, 0.60, 1],
}


# ---------------------------------------------------------------
# عناصر الواجهة (شكلها معرّف في ui.kv)
# ---------------------------------------------------------------
class StyledButton(Button):
    custom_bg = ListProperty([])


class NavButton(ToggleButton):
    pass


class CustomTextInput(TextInput):
    """حقل نص يعرض العربية مشكَّلة ومرتبة أثناء الكتابة (النص الحقيقي يبقى كما كتبه المستخدم)."""

    def _create_line_label(self, text, *args, **kwargs):
        hint = kwargs.get('hint', args[0] if args else False)
        try:
            if not hint and text and any('\u0600' <= c <= '\u06FF' for c in text):
                text = fix_arabic(text)
        except Exception:
            pass
        return super()._create_line_label(text, *args, **kwargs)


class LogoBox(StencilView, FloatLayout):
    """يقصّ ما يخرج عن حدوده، فيبدو اللوڨو طالعًا من وراء خانة الاسم."""


class BirthdayRow(BoxLayout):
    bname = StringProperty('')
    bdate = StringProperty('')
    name_text = StringProperty('')
    sub_text = StringProperty('')
    days_text = StringProperty('')
    days_color = ListProperty([0.18, 0.70, 0.40, 1])


DAYS_GREEN = [0.18, 0.70, 0.40, 1]
DAYS_ORANGE = [0.95, 0.60, 0.10, 1]
DAYS_RED = [0.90, 0.22, 0.25, 1]


def days_style(days):
    """نص ولون الأيام المتبقية: أخضر للبعيد، برتقالي خلال أسبوع، أحمر اليوم."""
    if days == 0:
        return 'Today!', DAYS_RED
    if days == 1:
        return 'Tomorrow', DAYS_ORANGE
    if days <= 7:
        return f'In {days} days', DAYS_ORANGE
    return f'In {days} days', DAYS_GREEN


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


class DatePopup(Popup):
    """نافذة اختيار التاريخ (يوم/شهر/سنة)، ومعها خانة اسم عند التعديل."""
    show_name = BooleanProperty(False)
    name_text = StringProperty('')
    date_text = StringProperty('')
    save_cb = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ids = self.ids
        ids.day_sp.values = [str(i) for i in range(1, 32)]
        ids.month_sp.values = MONTHS
        ids.year_sp.values = [str(y) for y in range(date.today().year, 1919, -1)]
        try:
            d = datetime.strptime(self.date_text, '%Y-%m-%d').date()
        except ValueError:
            d = date(2000, 1, 1)
        ids.day_sp.text = str(d.day)
        ids.month_sp.text = MONTHS[d.month - 1]
        ids.year_sp.text = str(d.year)
        if self.show_name:
            ids.name_in.text = self.name_text

    def confirm(self):
        ids = self.ids
        ids.err.text = ''
        name = ''
        if self.show_name:
            name = ids.name_in.text.strip()
            if not name:
                ids.err.text = 'Please enter a name'
                return
        try:
            y = int(ids.year_sp.text)
            m = MONTHS.index(ids.month_sp.text) + 1
            d = int(ids.day_sp.text)
            date_str = date(y, m, d).isoformat()
        except ValueError:
            ids.err.text = 'This date does not exist'
            return
        err = core.check_birth(date_str)
        if err:
            ids.err.text = err
            return
        cb = self.save_cb
        self.dismiss()
        if cb:
            cb(name, date_str)


class ConfirmPopup(Popup):
    """نافذة تأكيد (للحذف)."""
    msg = StringProperty('')
    sub = StringProperty('')
    yes_cb = ObjectProperty(None, allownone=True)

    def yes(self):
        cb = self.yes_cb
        self.dismiss()
        if cb:
            cb()


try:
    from gift_ui import GiftScreen, GiftCard
except Exception:
    GIFT_ERROR = traceback.format_exc()
    if core is not None:
        core.log(GIFT_ERROR)
    from kivy.uix.label import Label as _Label

    class GiftCard(BoxLayout):
        pass

    class GiftScreen(Screen):
        title_text = StringProperty('Gift tab failed to load')
        lang_label = StringProperty('')

        def toggle_lang(self):
            pass

        def on_kv_post(self, base_widget):
            Clock.schedule_once(self._show_error, 0.3)

        def _show_error(self, dt):
            lbl = _Label(text=GIFT_ERROR, font_size='11sp', size_hint_y=None,
                         halign='left', valign='top')
            lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
            lbl.bind(texture_size=lambda i, s: setattr(i, 'height', s[1] + 20))
            self.ids.content.add_widget(lbl)


try:
    from games_ui import GamesScreen
except Exception:
    GAMES_ERROR = traceback.format_exc()
    if core is not None:
        core.log(GAMES_ERROR)
    from kivy.uix.label import Label as _GLabel

    class GamesScreen(Screen):
        title_text = StringProperty('Games tab failed to load')
        lang_label = StringProperty('')

        def toggle_lang(self):
            pass

        def on_kv_post(self, base_widget):
            Clock.schedule_once(self._show_error, 0.3)

        def _show_error(self, dt):
            lbl = _GLabel(text=GAMES_ERROR, font_size='11sp', size_hint_y=None,
                          halign='left', valign='top')
            lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
            lbl.bind(texture_size=lambda i, s: setattr(i, 'height', s[1] + 20))
            self.ids.content.add_widget(lbl)


class SettingsScreen(Screen):
    pass


class BirthdaysScreen(Screen):
    birth_str = StringProperty('')
    rise = NumericProperty(0)  # 0 = اللوڨو مخبّأ، 1 = ظاهر

    def on_kv_post(self, base_widget):
        Clock.schedule_once(self.refresh_list, 0.2)
        self.queue_intro()

    def on_pre_enter(self, *args):
        self.refresh_list()
        self.queue_intro()

    def queue_intro(self):
        Clock.unschedule(self.play_intro)
        self.rise = 0
        Clock.schedule_once(self.play_intro, 0.15)

    def play_intro(self, *args):
        Animation.cancel_all(self, 'rise')
        self.rise = 0
        Animation(rise=1, duration=0.9, t='out_back').start(self)

    def refresh_list(self, *args):
        # قد يُستدعى أثناء بناء الشاشة قبل أن تكتمل عناصرها
        if 'list_layout' not in self.ids:
            Clock.schedule_once(self.refresh_list, 0.2)
            return
        layout = self.ids.list_layout
        layout.clear_widgets()

        rows = []
        for item in core.load_birthdays():
            try:
                rows.append((core.days_until(item['date']),
                             core.next_age(item['date']),
                             item['name'], item['date']))
            except Exception:
                continue

        rows.sort(key=lambda r: r[0])
        for days_left, age, name, date_str in rows:
            days_text, days_color = days_style(days_left)
            layout.add_widget(BirthdayRow(
                bname=name,
                bdate=date_str,
                name_text=fix_arabic(name),
                sub_text=f"Turns {age}  |  {date_str}",
                days_text=days_text,
                days_color=days_color,
            ))

    def open_date_picker(self):
        DatePopup(
            show_name=False,
            date_text=self.birth_str,
            save_cb=lambda n, d: setattr(self, 'birth_str', d),
        ).open()

    def edit_birthday(self, name, date_str):
        def save(new_name, new_date):
            app = App.get_running_app()
            items = core.load_birthdays()
            for b in items:
                if b['name'] == name and b['date'] == date_str:
                    b['name'] = new_name
                    b['date'] = new_date
                    break
            try:
                core.save_birthdays(items)
            except Exception as e:
                app.show_status(f"Save error: {e}")
                return
            self.refresh_list()
            app.show_status(core.check_and_notify())

        DatePopup(show_name=True, name_text=name, date_text=date_str,
                  save_cb=save).open()

    def add_birthday(self):
        app = App.get_running_app()
        name = self.ids.name_input.text.strip()
        date_str = self.birth_str.strip()

        if not name or not date_str:
            app.show_status("Please enter a name and pick a date")
            return

        err = core.check_birth(date_str)
        if err:
            app.show_status(err)
            return

        items = core.load_birthdays()
        items.append({'name': name, 'date': date_str})
        try:
            core.save_birthdays(items)
        except Exception as e:
            app.show_status(f"Save error: {e}")
            return

        self.ids.name_input.text = ""
        self.birth_str = ""
        self.refresh_list()
        # فحص فوري (مثلًا لو كان الموعد بعد 7 أيام أو يوم)
        app.show_status(core.check_and_notify())


# ---------------------------------------------------------------
# التطبيق
# ---------------------------------------------------------------
class BFBApp(App):
    ACCENTS = ACCENTS

    font = StringProperty(FONT_NAME)
    bg_color = ListProperty(THEMES['light']['bg'])
    card_color = ListProperty(THEMES['light']['card'])
    text_color = ListProperty(THEMES['light']['text'])
    muted_color = ListProperty(THEMES['light']['muted'])
    primary_color = ListProperty(ACCENTS['blue'])
    radius = NumericProperty(10)
    btn_height = NumericProperty(50)
    font_scale = NumericProperty(1.0)
    status = StringProperty('')
    status_color = ListProperty([0.85, 0.2, 0.2, 1])

    def build(self):
        self.build_failed = False
        if core is None:
            self.build_failed = True
            return error_screen(IMPORT_ERROR)
        try:
            Window.softinput_mode = 'below_target'
            self.prefs = core.load_settings()
            self.apply_prefs()
            kv_path = os.path.join(BASE_DIR, 'ui.kv')
            if not os.path.exists(kv_path):
                files = ', '.join(sorted(os.listdir(BASE_DIR)))
                raise FileNotFoundError(f"ui.kv not found in {BASE_DIR}\nFiles: {files}")
            return Builder.load_file(kv_path)
        except Exception:
            self.build_failed = True
            tb = traceback.format_exc()
            try:
                core.log(tb)
            except Exception:
                pass
            return error_screen(tb + ("\nFONT: " + FONT_ERROR if FONT_ERROR else ""))

    # ---------- الإعدادات ----------
    def apply_prefs(self):
        theme = THEMES.get(self.prefs.get('theme'), THEMES['light'])
        self.bg_color = theme['bg']
        self.card_color = theme['card']
        self.text_color = theme['text']
        self.muted_color = theme['muted']
        self.primary_color = ACCENTS.get(self.prefs.get('accent'), ACCENTS['blue'])
        self.radius = float(self.prefs.get('radius', 10))
        self.btn_height = float(self.prefs.get('btn_height', 50))
        self.font_scale = float(self.prefs.get('font_scale', 1.0))

    def _save_later(self):
        Clock.unschedule(self._save_prefs)
        Clock.schedule_once(self._save_prefs, 0.6)

    def _save_prefs(self, *args):
        try:
            core.save_settings(self.prefs)
        except Exception as e:
            core.log(f"save settings: {e}")

    def set_theme(self, name):
        self.prefs['theme'] = name
        self.apply_prefs()
        self._save_later()

    def set_accent(self, name):
        self.prefs['accent'] = name
        self.apply_prefs()
        self._save_later()

    def set_radius(self, value):
        if abs(self.radius - value) < 0.001:
            return
        self.prefs['radius'] = float(value)
        self.radius = float(value)
        self._save_later()

    def set_btn_height(self, value):
        if abs(self.btn_height - value) < 0.001:
            return
        self.prefs['btn_height'] = float(value)
        self.btn_height = float(value)
        self._save_later()

    def set_font_scale(self, value):
        if abs(self.font_scale - value) < 0.001:
            return
        self.prefs['font_scale'] = round(float(value), 2)
        self.font_scale = round(float(value), 2)
        self._save_later()

    def reset_settings(self):
        self.prefs = dict(core.DEFAULT_SETTINGS)
        self.apply_prefs()
        self._save_later()

    # ---------- التنقل ----------
    def go(self, screen_name):
        self.root.ids.sm.current = screen_name

    # ---------- الحالة والإشعارات ----------
    def show_status(self, errors, ok=False):
        if not errors:
            self.status = ''
            return
        if isinstance(errors, str):
            msg = errors
        else:
            msg = "Notification error: " + str(errors[0])
        self.status = msg
        self.status_color = [0.1, 0.6, 0.2, 1] if ok else [0.85, 0.2, 0.2, 1]

    def test_notification(self):
        ok, err = core.test_notification()
        if ok:
            self.show_status(
                "Notification sent. If you see nothing, check phone settings.",
                ok=True)
        else:
            self.show_status("Error: " + err)

    # ---------- نسخة احتياطية ----------
    def export_backup(self):
        try:
            code = core.export_backup()
            text = "BFB backup - keep this message safe:\n" + code
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(text)
            if platform == 'android':
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                JString = autoclass('java.lang.String')
                intent = Intent(Intent.ACTION_SEND)
                intent.setType('text/plain')
                intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', JString(text)))
                chooser = Intent.createChooser(intent, cast('java.lang.CharSequence', JString('BFB')))
                PythonActivity.mActivity.startActivity(chooser)
            self.show_status("Backup copied. Save it somewhere safe (e.g. send it to yourself).",
                             ok=True)
        except Exception as e:
            self.show_status(f"Backup error: {e}")

    def import_backup(self):
        try:
            from kivy.core.clipboard import Clipboard
            added, skipped = core.import_backup(Clipboard.paste() or '')
        except ValueError:
            self.show_status("No valid backup found in the clipboard. Copy the backup message first.")
            return
        except Exception as e:
            self.show_status(f"Import error: {e}")
            return
        self.prefs = core.load_settings()
        self.apply_prefs()
        try:
            self.root.ids.sm.get_screen('birthdays').refresh_list()
        except Exception:
            pass
        self.show_status(f"Backup restored: {added} added, {skipped} already existed.", ok=True)

    # ---------- بيانات ----------
    def edit_birthday(self, name, date_str):
        self.root.ids.sm.get_screen('birthdays').edit_birthday(name, date_str)

    def ask_delete(self, name, date_str):
        ConfirmPopup(
            msg='Delete this birthday?',
            sub=fix_arabic(name),
            yes_cb=lambda: self.delete_birthday(name, date_str),
        ).open()

    def delete_birthday(self, name, date_str):
        items = [
            b for b in core.load_birthdays()
            if not (b['name'] == name and b['date'] == date_str)
        ]
        try:
            core.save_birthdays(items)
        except Exception as e:
            self.show_status(f"Delete error: {e}")
        self.root.ids.sm.get_screen('birthdays').refresh_list()

    # ---------- التشغيل ----------
    def on_start(self):
        if getattr(self, 'build_failed', False):
            return
        if platform == 'android':
            try:
                from android.permissions import request_permissions
                request_permissions(
                    ['android.permission.POST_NOTIFICATIONS'],
                    lambda perms, grants: self.start_background()
                )
            except Exception as e:
                core.log(f"permission error: {e}")
                self.start_background()
        else:
            Clock.schedule_once(lambda dt: self.show_status(core.check_and_notify()), 1)

    def start_background(self, *args):
        try:
            self.show_status(core.check_and_notify())
        except Exception as e:
            core.log(f"start check: {e}")
        try:
            from android import AndroidService
            svc = AndroidService('BFB Reminder', 'تذكير أعياد الميلاد يعمل')
            svc.start('service started')
        except Exception as e:
            core.log(f"service error: {e}")


if __name__ == '__main__':
    BFBApp().run()
