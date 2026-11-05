import os
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import platform
from datetime import datetime

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

    def fix_arabic(text):
        try:
            return get_display(arabic_reshaper.reshape(text))
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
    pass


class BirthdayRow(BoxLayout):
    info = StringProperty('')
    bname = StringProperty('')
    bdate = StringProperty('')


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


class GamesScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class BirthdaysScreen(Screen):
    def on_kv_post(self, base_widget):
        Clock.schedule_once(self.refresh_list, 0.2)

    def on_pre_enter(self, *args):
        self.refresh_list()

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
                rows.append((core.days_until(item['date']), item['name'], item['date']))
            except Exception:
                continue

        rows.sort(key=lambda r: r[0])
        for days_left, name, date_str in rows:
            info = (
                f"Days left: {days_left}  |  Name: {fix_arabic(name)}\n"
                f"Birth date: {date_str}"
            )
            layout.add_widget(BirthdayRow(info=info, bname=name, bdate=date_str))

    def add_birthday(self):
        app = App.get_running_app()
        name = self.ids.name_input.text.strip()
        date_str = self.ids.date_input.text.strip()

        if not name or not date_str:
            app.show_status("Please enter a name and a date")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            app.show_status("Wrong date format. Use YYYY-MM-DD")
            return

        items = core.load_birthdays()
        items.append({'name': name, 'date': date_str})
        try:
            core.save_birthdays(items)
        except Exception as e:
            app.show_status(f"Save error: {e}")
            return

        self.ids.name_input.text = ""
        self.ids.date_input.text = ""
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

    # ---------- بيانات ----------
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
