import os

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import platform
from datetime import datetime

import core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(BASE_DIR, 'Cairo-Regular.ttf')
ACTIVE_FONT = FONT_FILE if os.path.exists(FONT_FILE) else 'Roboto'

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


KV_CODE = '''
<CustomTextInput>:
    multiline: False
    font_name: "FONTPATH"
    font_size: "16sp"
    padding: [15, 15, 15, 15]
    background_color: 0, 0, 0, 0
    foreground_color: 0.2, 0.2, 0.2, 1

<BirthdayScreen>:
    orientation: 'vertical'
    padding: 20
    spacing: 15
    canvas.before:
        Color:
            rgba: 0.94, 0.95, 0.97, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "BFB Reminder"
        font_name: "FONTPATH"
        font_size: '26sp'
        bold: True
        color: 0.1, 0.4, 0.7, 1
        size_hint_y: None
        height: '50dp'
        halign: 'center'

    BoxLayout:
        size_hint_y: None
        height: '50dp'
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        CustomTextInput:
            id: name_input
            hint_text: "Enter Name"

    BoxLayout:
        size_hint_y: None
        height: '50dp'
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        CustomTextInput:
            id: date_input
            hint_text: "YYYY-MM-DD"

    Button:
        text: "Add Birthday"
        font_name: "FONTPATH"
        font_size: '16sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '50dp'
        background_normal: ''
        background_down: ''
        background_color: 0, 0, 0, 0
        on_press: root.add_birthday()
        canvas.before:
            Color:
                rgba: 0.1, 0.5, 0.8, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]

    ScrollView:
        size_hint: (1, 1)
        BoxLayout:
            id: list_layout
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: 10
            padding: 5
'''.replace("FONTPATH", FONT_FILE.replace("\\", "/"))

Builder.load_string(KV_CODE)


class CustomTextInput(TextInput):
    pass


class BirthdayScreen(BoxLayout):
    def on_kv_post(self, base_widget):
        Clock.schedule_once(lambda dt: self.refresh_list(), 0.2)

    def refresh_list(self):
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
            layout.add_widget(self.build_row(name, days_left, date_str))

    def build_row(self, name, days_left, date_str):
        info_text = f"Days left: {days_left}  |  Name: {fix_arabic(name)}"

        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='55dp',
            padding=10,
            spacing=10,
        )

        with row.canvas.before:
            Color(1, 1, 1, 1)
            row.rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[8, ])

        def update_rect(inst, _):
            inst.rect.pos = inst.pos
            inst.rect.size = inst.size

        row.bind(pos=update_rect, size=update_rect)

        label = Label(
            text=info_text,
            font_name=ACTIVE_FONT,
            size_hint_x=0.75,
            color=(0.2, 0.2, 0.2, 1),
            font_size='14sp',
            halign='left',
            valign='middle',
        )
        label.bind(size=lambda s, _: setattr(s, 'text_size', s.size))

        btn = Button(
            text="Delete",
            font_name=ACTIVE_FONT,
            size_hint_x=0.25,
            color=(1, 1, 1, 1),
            background_normal='',
            background_down='',
            background_color=(0, 0, 0, 0),
        )
        with btn.canvas.before:
            Color(0.85, 0.2, 0.2, 1)
            btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[6, ])
        btn.bind(pos=update_rect, size=update_rect)
        btn.bind(on_press=lambda x: self.delete_birthday(name, date_str))

        row.add_widget(label)
        row.add_widget(btn)
        return row

    def delete_birthday(self, name, date_str):
        items = [
            b for b in core.load_birthdays()
            if not (b['name'] == name and b['date'] == date_str)
        ]
        try:
            core.save_birthdays(items)
        except Exception as e:
            print(f"[خطأ أثناء الحذف]: {e}")
        self.refresh_list()

    def add_birthday(self):
        name = self.ids.name_input.text.strip()
        date_str = self.ids.date_input.text.strip()

        if not name or not date_str:
            print("الرجاء إدخال الاسم والتاريخ!")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("تنسيق التاريخ غير صحيح، استعمل YYYY-MM-DD")
            return

        items = core.load_birthdays()
        items.append({'name': name, 'date': date_str})
        try:
            core.save_birthdays(items)
        except Exception as e:
            print(f"[خطأ في الحفظ]: {e}")
            return

        self.ids.name_input.text = ""
        self.ids.date_input.text = ""
        self.refresh_list()
        # فحص فوري (مثلًا لو كان الموعد بعد 7 أيام أو يوم)
        try:
            core.check_and_notify()
        except Exception as e:
            print(f"[notify error]: {e}")


class BFBApp(App):
    def build(self):
        return BirthdayScreen()

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions
                request_permissions(
                    ['android.permission.POST_NOTIFICATIONS'],
                    lambda perms, grants: self.start_background()
                )
            except Exception as e:
                print(f"[permission error]: {e}")
                self.start_background()
        else:
            Clock.schedule_once(lambda dt: core.check_and_notify(), 1)

    def start_background(self, *args):
        try:
            core.check_and_notify()
        except Exception as e:
            print(f"[notify error]: {e}")
        try:
            from android import AndroidService
            svc = AndroidService('BFB Reminder', 'تذكير أعياد الميلاد يعمل')
            svc.start('service started')
        except Exception as e:
            print(f"[service error]: {e}")


if __name__ == '__main__':
    BFBApp().run()