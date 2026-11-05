"""شاشة الألعاب: قائمة ألعاب (تُضاف ألعاب جديدة تباعًا). أولها: من يعرفني أكثر؟"""
import os
import re
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen

import core
import game_data as gd

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


PREFS_FILE = os.path.join(core.data_dir(), 'gift_prefs.json')   # اللغة مشتركة مع تبويب الهدايا
GRAY = [0.45, 0.47, 0.52, 1]
GREEN = [0.15, 0.62, 0.30, 1]
RED = [0.85, 0.22, 0.25, 1]
HAS_ARABIC = re.compile('[؀-ۿ]')

# نصوص الواجهة (إنجليزي، عربي)
S = {
    'title': ('Games', 'الألعاب'),
    'choose': ('Choose a game', 'اختر لعبة'),
    'soon': ('More games are coming soon...', 'المزيد من الألعاب قريبًا...'),
    'play': ('Play', 'العب'),
    'k_title': ('Who knows me best?', 'من يعرفني أكثر؟'),
    'k_desc': ('Answer 10 questions about yourself, send the code to a friend, and see how many they guess right.',
               'أجب عن 10 أسئلة عن نفسك، وأرسل الكود إلى صديقك لترى كم إجابة سيخمّنها صحيحة.'),
    'create': ('Create my quiz', 'أنشئ اختباري'),
    'have_code': ('I received a code', 'وصلني كود من صديق'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'back': ('Back', 'رجوع'),
    'name_head': ('What is your name?', 'ما اسمك؟'),
    'name_hint': ('Your friend will see this name.', 'سيرى صديقك هذا الاسم.'),
    'name_ph': ('Your name', 'اسمك'),
    'cont': ('Continue', 'متابعة'),
    'empty_name': ('Please enter your name.', 'الرجاء إدخال اسمك.'),
    'about_you': ('Answer about yourself', 'أجب عن نفسك'),
    'guess': ("Guess {name}'s answer", 'خمّن إجابة {name}'),
    'progress': ('Question {i} of {n}', 'السؤال {i} من {n}'),
    'done_head': ('Your quiz is ready!', 'اختبارك جاهز!'),
    'done_body': ('Send this code to your friend. They open the app, go to Games, and paste it.',
                  'أرسل هذا الكود إلى صديقك. يفتح التطبيق ثم الألعاب ثم يلصقه.'),
    'copy': ('Copy code', 'نسخ الكود'),
    'copied': ('Code copied.', 'تم نسخ الكود.'),
    'share': ('Share', 'مشاركة'),
    'newquiz': ('Create another quiz', 'أنشئ اختبارًا آخر'),
    'code_head': ('Paste the code you received', 'الصق الكود الذي وصلك'),
    'code_ph': ('BFB-XXXXX-XXXXX-...', 'BFB-XXXXX-XXXXX-...'),
    'paste': ('Paste', 'لصق'),
    'start': ('Start', 'ابدأ'),
    'bad_code': ('This code is not valid. Check that you copied all of it.',
                 'هذا الكود غير صالح. تأكد أنك نسخته كاملًا.'),
    'guest_head': ('How well do you know {name}?', 'هل تعرف {name} جيدًا؟'),
    'score_head': ('Your score', 'نتيجتك'),
    'right': ('Correct', 'صحيحة'),
    'wrong': ('Wrong', 'خاطئة'),
    'correct_ans': ('Correct answer: {a}', 'الإجابة الصحيحة: {a}'),
    'your_ans': ('Your answer: {a}', 'إجابتك: {a}'),
    'again': ('Try another code', 'جرّب كودًا آخر'),
    'res10': ('Perfect! You know {name} better than anyone!', 'ممتاز! تعرف {name} أكثر من أي أحد!'),
    'res8': ("Amazing! You are one of {name}'s closest friends.", 'رائع! أنت من أقرب أصدقاء {name}.'),
    'res5': ('Not bad! You know {name} quite well.', 'ليس سيئًا! تعرف {name} جيدًا.'),
    'res3': ('Hmm... you still have things to learn about {name}.', 'همم... ما زال عليك أن تتعرف على {name} أكثر.'),
    'res0': ('Oops! Time to spend more time with {name}!', 'حان وقت قضاء وقت أطول مع {name}!'),
    'share_en': ('Think you know me well? Open the BFB app > Games > Who knows me best? > '
                 'I received a code, and paste the code below:'),
    'share_ar': ('هل تعرفني جيدًا؟ افتح تطبيق BFB ثم الألعاب ثم من يعرفني أكثر؟ '
                 'ثم وصلني كود، والصق الكود أدناه:'),
}

# قائمة الألعاب: (المعرّف، العنوان، الوصف). لإضافة لعبة جديدة أضف سطرًا هنا وفرعًا في open_game.
GAMES = [('knowme', 'k_title', 'k_desc')]


def share_text(text):
    """يفتح قائمة المشاركة في أندرويد (إنستغرام، واتساب...)."""
    from kivy.utils import platform
    if platform != 'android':
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)
        raise RuntimeError('Sharing works on Android only (text was copied).')
    from jnius import autoclass, cast
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    JString = autoclass('java.lang.String')
    intent = Intent(Intent.ACTION_SEND)
    intent.setType('text/plain')
    intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', JString(text)))
    chooser = Intent.createChooser(intent, cast('java.lang.CharSequence', JString('BFB')))
    PythonActivity.mActivity.startActivity(chooser)


class GamesScreen(Screen):
    title_text = StringProperty('')
    lang_label = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang = self.saved_lang()
        self.stage = 'menu'
        self.status = ''
        self.status_ok = False
        self.host_name = ''
        self.host_qids = []
        self.host_answers = []
        self.code = ''
        self.code_text = ''
        self.guest = None
        self.guest_answers = []
        self.qi = 0
        self._name_ti = None
        self._code_ti = None

    # ---------- دورة الحياة ----------
    def on_kv_post(self, base_widget):
        Clock.schedule_once(lambda dt: self.render(), 0.2)

    def on_pre_enter(self, *args):
        self.lang = self.saved_lang()
        self.render()

    def saved_lang(self):
        prefs = core._read(PREFS_FILE, {})
        lang = prefs.get('lang') if isinstance(prefs, dict) else None
        return lang if lang in ('en', 'ar') else 'en'

    # ---------- مساعدات النص ----------
    def is_ar(self):
        return self.lang == 'ar'

    def tx(self, key, fs=16, pad=60, **fmt):
        en, ar = S[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def pair(self, en, ar, fs=16, pad=60, **fmt):
        text = ar if self.is_ar() else en
        if fmt:
            text = text.format(**fmt)
        return self.shape(text, fs, pad)

    def shape(self, text, fs=16, pad=60):
        if not self.is_ar():
            return text
        width_dp = Window.width / dp(1)
        max_chars = max(12, int((width_dp - pad) / (fs * 0.55)))
        lines, cur = [], ''
        for w in text.split():
            if cur and len(cur) + 1 + len(w) > max_chars:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + ' ' + w) if cur else w
        if cur:
            lines.append(cur)
        return '\n'.join(fix_arabic(l) for l in lines)

    def disp_name(self, name):
        """اسم الصديق: في الواجهة الإنجليزية نشكّله بنفسنا، وفي العربية يشكّله shape()."""
        if not self.is_ar() and HAS_ARABIC.search(name or ''):
            return fix_arabic(name)
        return name

    def opt_text(self, qid, idx):
        en, ar = gd.POOL[qid][2][idx]
        return ar if self.is_ar() else en

    # ---------- بناء العناصر ----------
    def label(self, text, fs=16, bold=False, color=None, halign='center'):
        app = App.get_running_app()
        lbl = Label(
            text=text, font_name=app.font, font_size=sp(fs) * app.font_scale,
            bold=bold, color=color or app.text_color,
            halign=halign, valign='middle', size_hint_y=None, height=dp(30),
        )
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        lbl.bind(texture_size=lambda inst, s: setattr(inst, 'height', s[1] + dp(8)))
        return lbl

    def button(self, text, on_release, gray=False):
        app = App.get_running_app()
        btn = Factory.StyledButton(text=text)
        if gray:
            btn.custom_bg = GRAY
        lines = text.count('\n') + 1
        btn.height = max(dp(app.btn_height), dp(22) * lines + dp(26))
        btn.bind(on_release=lambda *a: on_release())
        return btn

    def entry(self, hint, text='', multiline=False, height=None):
        app = App.get_running_app()
        box = BoxLayout(size_hint_y=None, height=height or dp(app.btn_height))
        with box.canvas.before:
            Color(*app.card_color)
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(app.radius)])
        box.bind(pos=lambda i, v: setattr(rect, 'pos', i.pos),
                 size=lambda i, v: setattr(rect, 'size', i.size))
        ti = Factory.CustomTextInput(hint_text=hint, text=text, multiline=multiline)
        box.add_widget(ti)
        return box, ti

    # ---------- العرض ----------
    def capture(self):
        """يحفظ ما كتبه المستخدم قبل إعادة بناء الشاشة."""
        try:
            if self._name_ti is not None:
                self.host_name = self._name_ti.text
            if self._code_ti is not None:
                self.code_text = self._code_ti.text
        except Exception:
            pass
        self._name_ti = None
        self._code_ti = None

    def render(self):
        if 'content' not in self.ids:
            return
        self.capture()
        box = self.ids.content
        box.clear_widgets()
        self.title_text = self.tx('title', 22, 150)
        self.lang_label = fix_arabic('عربي') if not self.is_ar() else 'English'
        try:
            getattr(self, 'show_' + self.stage)(box)
            if self.status:
                app = App.get_running_app()
                box.add_widget(self.label(self.status, fs=13,
                                          color=GREEN if self.status_ok else RED))
        except Exception:
            box.clear_widgets()
            box.add_widget(self.label(traceback.format_exc(), fs=11, halign='left'))
        self.ids.scroll.scroll_y = 1

    def go(self, stage):
        self.capture()
        self.stage = stage
        self.status = ''
        self.render()

    def set_status(self, text, ok=False):
        self.status = text
        self.status_ok = ok
        self.render()

    # ---------- قائمة الألعاب ----------
    def show_menu(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('choose', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        halign = 'right' if self.is_ar() else 'left'
        for gid, tkey, dkey in GAMES:
            card = Factory.GiftCard()
            card.add_widget(self.label(self.tx(tkey, 18, 90), fs=18, bold=True, halign=halign))
            card.add_widget(self.label(self.tx(dkey, 13, 90), fs=13, color=app.muted_color,
                                       halign=halign))
            card.add_widget(self.button(self.tx('play', 16, 100),
                                        lambda g=gid: self.open_game(g)))
            box.add_widget(card)
        box.add_widget(self.label(self.tx('soon', 13, 60), fs=13, color=app.muted_color))

    def open_game(self, gid):
        if gid == 'knowme':
            self.go('home')

    # ---------- من يعرفني أكثر: الصفحة الأولى ----------
    def show_home(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('k_title', 22, 60), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('k_desc', 15, 60), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.tx('create', 16, 100), self.start_host))
        box.add_widget(self.button(self.tx('have_code', 16, 100),
                                   lambda: self.go('guest_code')))
        box.add_widget(self.button(self.tx('menu', 15, 100), lambda: self.go('menu'), gray=True))

    # ---------- المضيف: الاسم ثم الأسئلة ثم الكود ----------
    def start_host(self):
        self.go('host_name')

    def show_host_name(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('name_head', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('name_hint', 14, 60), fs=14, color=app.muted_color))
        row, self._name_ti = self.entry(self.tx('name_ph', 16, 100), text=self.host_name)
        box.add_widget(row)
        box.add_widget(self.button(self.tx('cont', 16, 100), self.begin_host_quiz))
        box.add_widget(self.button(self.tx('back', 15, 100), lambda: self.go('home'), gray=True))

    def begin_host_quiz(self):
        self.capture()
        name = (self.host_name or '').strip()
        if not name:
            self.set_status(self.tx('empty_name', 13, 60))
            return
        self.host_name = name
        self.host_qids = gd.pick_question_ids()
        self.host_answers = []
        self.qi = 0
        self.go('host_quiz')

    def show_host_quiz(self, box):
        app = App.get_running_app()
        n = len(self.host_qids)
        qid = self.host_qids[self.qi]
        box.add_widget(self.label(self.tx('progress', 13, 60, i=self.qi + 1, n=n),
                                  fs=13, color=app.muted_color))
        box.add_widget(ProgressBar(max=n, value=self.qi + 1, size_hint_y=None, height=dp(8)))
        box.add_widget(self.label(self.tx('about_you', 14, 60), fs=14, color=app.primary_color))
        self.question_widgets(box, qid, self.host_answer, self.host_back)

    def question_widgets(self, box, qid, on_pick, on_back):
        en, ar, options = gd.POOL[qid]
        box.add_widget(self.label(self.pair(en, ar, 20, 50), fs=20, bold=True))
        for idx, (o_en, o_ar) in enumerate(options):
            box.add_widget(self.button(self.pair(o_en, o_ar, 15, 110),
                                       lambda i=idx: on_pick(i)))
        box.add_widget(self.button(self.tx('back', 15, 100), on_back, gray=True))

    def host_answer(self, idx):
        self.host_answers.append(idx)
        if len(self.host_answers) < len(self.host_qids):
            self.qi += 1
            self.render()
        else:
            qa = list(zip(self.host_qids, self.host_answers))
            self.code = gd.encode(self.host_name, qa)
            self.go('host_done')

    def host_back(self):
        if self.host_answers:
            self.host_answers.pop()
            self.qi = max(0, self.qi - 1)
            self.render()
        else:
            self.go('host_name')

    def show_host_done(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('done_head', 22, 60), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('done_body', 15, 60), fs=15, color=app.muted_color))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.code, fs=15, bold=True))
        box.add_widget(card)
        box.add_widget(self.button(self.tx('copy', 16, 100), self.copy_code))
        box.add_widget(self.button(self.tx('share', 16, 100), self.share_code))
        box.add_widget(self.button(self.tx('newquiz', 15, 100), self.start_host, gray=True))
        box.add_widget(self.button(self.tx('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def copy_code(self):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.code)
            self.set_status(self.tx('copied', 13, 60), ok=True)
        except Exception as e:
            self.set_status(f"Error: {e}")

    def share_code(self):
        text = f"\U0001F382 {S['share_en']}\n{S['share_ar']}\n\n{self.code}"
        try:
            share_text(text)
        except Exception as e:
            self.set_status(f"{e}")

    # ---------- الصديق: لصق الكود ثم الأسئلة ثم النتيجة ----------
    def show_guest_code(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('code_head', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        row, self._code_ti = self.entry(self.tx('code_ph', 14, 100), text=self.code_text,
                                        multiline=True, height=dp(110))
        box.add_widget(row)
        box.add_widget(self.button(self.tx('paste', 15, 100), self.paste_code, gray=True))
        box.add_widget(self.button(self.tx('start', 16, 100), self.begin_guest))
        box.add_widget(self.button(self.tx('back', 15, 100), lambda: self.go('home'), gray=True))

    def paste_code(self):
        try:
            from kivy.core.clipboard import Clipboard
            text = Clipboard.paste() or ''
        except Exception as e:
            self.set_status(f"Error: {e}")
            return
        self.code_text = text
        if self._code_ti is not None:
            self._code_ti.text = text

    def begin_guest(self):
        self.capture()
        try:
            self.guest = gd.decode(self.code_text)
        except ValueError:
            self.set_status(self.tx('bad_code', 13, 60))
            return
        self.guest_answers = []
        self.qi = 0
        self.go('guest_quiz')

    def show_guest_quiz(self, box):
        app = App.get_running_app()
        qa = self.guest['qa']
        n = len(qa)
        name = self.disp_name(self.guest['name'])
        qid = qa[self.qi][0]
        box.add_widget(self.label(self.tx('progress', 13, 60, i=self.qi + 1, n=n),
                                  fs=13, color=app.muted_color))
        box.add_widget(ProgressBar(max=n, value=self.qi + 1, size_hint_y=None, height=dp(8)))
        box.add_widget(self.label(self.tx('guess', 14, 60, name=name), fs=14,
                                  color=app.primary_color))
        self.question_widgets(box, qid, self.guest_answer, self.guest_back)

    def guest_answer(self, idx):
        self.guest_answers.append(idx)
        if len(self.guest_answers) < len(self.guest['qa']):
            self.qi += 1
            self.render()
        else:
            self.go('guest_result')

    def guest_back(self):
        if self.guest_answers:
            self.guest_answers.pop()
            self.qi = max(0, self.qi - 1)
            self.render()
        else:
            self.go('guest_code')

    def show_guest_result(self, box):
        app = App.get_running_app()
        qa = self.guest['qa']
        n = len(qa)
        name = self.disp_name(self.guest['name'])
        s = gd.score(qa, self.guest_answers)
        key = 'res10' if s == n else 'res8' if s >= 8 else 'res5' if s >= 5 else 'res3' if s >= 3 else 'res0'
        box.add_widget(self.label(self.tx('score_head', 16, 60), fs=16, color=app.muted_color))
        box.add_widget(self.label(f"{s} / {n}", fs=40, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.tx(key, 17, 60, name=name), fs=17, bold=True))

        halign = 'right' if self.is_ar() else 'left'
        for (qid, correct), guess in zip(qa, self.guest_answers):
            q_en, q_ar, _ = gd.POOL[qid]
            ok = guess == correct
            card = Factory.GiftCard()
            card.add_widget(self.label(self.pair(q_en, q_ar, 15, 90), fs=15, bold=True,
                                       halign=halign))
            card.add_widget(self.label(self.tx('right' if ok else 'wrong', 13, 90), fs=13,
                                       bold=True, color=GREEN if ok else RED, halign=halign))
            card.add_widget(self.label(
                self.tx('your_ans', 13, 90, a=self.opt_text(qid, guess)),
                fs=13, color=app.muted_color, halign=halign))
            if not ok:
                card.add_widget(self.label(
                    self.tx('correct_ans', 13, 90, a=self.opt_text(qid, correct)),
                    fs=13, color=app.muted_color, halign=halign))
            box.add_widget(card)
        box.add_widget(self.button(self.tx('again', 15, 100), lambda: self.go('guest_code')))
        box.add_widget(self.button(self.tx('menu', 15, 100), lambda: self.go('menu'), gray=True))

    # ---------- اللغة ----------
    def toggle_lang(self):
        self.capture()
        self.lang = 'ar' if self.lang == 'en' else 'en'
        try:
            core._write(PREFS_FILE, {'lang': self.lang})
        except Exception as e:
            core.log(f"games prefs: {e}")
        self.render()
