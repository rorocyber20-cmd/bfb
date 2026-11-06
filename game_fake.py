"""لعبة «المؤقت المخادع»: هاتف واحد، إشارات مزيفة، والضغط فقط عند GO الأخضر."""
import random
import re
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

GRAY = [0.45, 0.47, 0.52, 1]
READY = ('Get ready...', 'استعدوا...', (0.30, 0.30, 0.36, 1))
REAL = ('GO!', 'انطلق!', (0.10, 0.72, 0.28, 1))
FAKES = [
    ('GO!', 'انطلق!', (0.95, 0.80, 0.15, 1)),
    ('NOW!', 'الآن!', (0.95, 0.50, 0.10, 1)),
    ('PRESS!', 'اضغط!', (0.20, 0.50, 0.90, 1)),
    ('GO?', 'انطلق؟', (0.60, 0.30, 0.80, 1)),
    ('Wait...', 'انتظر...', (0.85, 0.25, 0.25, 1)),
    ('GO!!', 'انطلق!!', (0.90, 0.35, 0.60, 1)),
    ('Almost...', 'تقريبًا...', (0.15, 0.60, 0.65, 1)),
]

FT = {
    'head': ('Fake Timer', 'المؤقت المخادع'),
    'rules': ('One phone, 2 to 4 players. The screen will show fake signals to trick you. '
              'Press your button ONLY when the screen turns GREEN and says GO! '
              'The first to press wins the round. Pressing too early puts you out of the round.',
              'هاتف واحد، من 2 إلى 4 لاعبين. ستعرض الشاشة إشارات مزيفة لخداعكم. '
              'اضغط زرك فقط عندما تصبح الشاشة خضراء وتكتب انطلق! '
              'أول من يضغط يفوز بالجولة، ومن يضغط مبكرًا يخرج من الجولة.'),
    'names_hint': ('Player names, separated by commas', 'أسماء اللاعبين مفصولة بفواصل'),
    'names_ph': ('Rayan, Mohamed', 'ريان ، محمد'),
    'points': ('Points to win the match', 'نقاط الفوز بالمباراة'),
    'need': ('Please enter 2 to 4 different names.', 'الرجاء إدخال من 2 إلى 4 أسماء مختلفة.'),
    'start': ('Start', 'ابدأ'),
    'round': ('Round {i}', 'الجولة {i}'),
    'ready_hint': ('Everyone put a finger near their button. Press only on GREEN GO!',
                   'ضعوا أصابعكم قرب أزرارهم. اضغطوا فقط عند انطلق! الخضراء.'),
    'begin': ('Start the round', 'ابدأ الجولة'),
    'out': ('{name} (out)', '{name} (خرج)'),
    'wins': ('{name} wins the round!', '{name} يفوز بالجولة!'),
    'ms': ('Reaction time: {ms} ms', 'زمن الاستجابة: {ms} مللي ثانية'),
    'early': ('Everyone else pressed too early!', 'ضغط الجميع مبكرًا ما عداه!'),
    'none': ('Nobody won this round.', 'لا أحد فاز بهذه الجولة.'),
    'slow': ('Too slow! Nobody pressed in time.', 'بطيئون! لم يضغط أحد في الوقت المناسب.'),
    'line': ('{name}: {n}', '{name}: {n}'),
    'next': ('Next round', 'الجولة التالية'),
    'champ': ('{name} wins the match!', '{name} يفوز بالمباراة!'),
    'again': ('Play again', 'العب مجددًا'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def parse_names(text, limit=4):
    out, seen = [], set()
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:14]
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out[:limit]


class FakeTimerMixin:
    def ft_init(self):
        self.ft_players = []
        self.ft_scores = []
        self.ft_target = 3
        self.ft_round = 1
        self.ft_state = 'idle'
        self.ft_out = set()
        self.ft_events = []
        self.ft_go_time = 0.0
        self.ft_last = (None, None, 'none')
        self._ft_color = None
        self._ft_lbl = None
        self._ft_btns = []

    def ft_stop(self):
        for ev in getattr(self, 'ft_events', []):
            try:
                ev.cancel()
            except Exception:
                pass
        self.ft_events = []

    def fk(self, key, fs=16, pad=60, **fmt):
        en, ar = FT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    # ---------- الإعداد ----------
    def show_ft_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.fk('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.fk('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.fk('names_hint', 14), fs=14, color=app.muted_color))
        row, _ = self.entry(self.fk('names_ph', 15, 100), key='ft_names')
        box.add_widget(row)
        box.add_widget(self.label(self.fk('points', 15), fs=15, bold=True))
        sel = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        for n in (3, 5):
            b = Factory.StyledButton(text=str(n))
            if n != self.ft_target:
                b.custom_bg = GRAY
            b.bind(on_release=lambda inst, n=n: self.ft_set_target(n))
            sel.add_widget(b)
        box.add_widget(sel)
        box.add_widget(self.button(self.fk('start', 16, 100), self.ft_start))
        box.add_widget(self.button(self.fk('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ft_set_target(self, n):
        self.ft_target = n
        self.render()

    def ft_start(self):
        self.snapshot()
        names = parse_names(self.form.get('ft_names', ''))
        if len(names) < 2:
            self.set_status(self.fk('need', 13))
            return
        self.ft_players = names
        self.ft_reset()
        self.go('ft_ready')

    def ft_reset(self):
        self.ft_scores = [0] * len(self.ft_players)
        self.ft_round = 1

    def score_lines(self, box, fs=16):
        for nm, sc in zip(self.ft_players, self.ft_scores):
            box.add_widget(self.label(self.fk('line', fs, 60, name=self.disp_name(nm), n=sc),
                                      fs=fs))

    def show_ft_ready(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.fk('round', 24, 60, i=self.ft_round), fs=24, bold=True,
                                  color=app.primary_color))
        self.score_lines(box)
        box.add_widget(self.label(self.fk('ready_hint', 15), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.fk('begin', 17, 100), self.ft_begin))
        box.add_widget(self.button(self.fk('back', 15, 100), lambda: self.go('ft_setup'),
                                   gray=True))

    # ---------- الجولة ----------
    def ft_begin(self):
        self.ft_state = 'wait'
        self.ft_out = set()
        self.go('ft_play')

    def show_ft_play(self, box):
        app = App.get_running_app()
        panel = BoxLayout(size_hint_y=None, height=dp(230), padding=dp(10))
        with panel.canvas.before:
            self._ft_color = Color(*READY[2])
            rect = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(app.radius) * 2])
        panel.bind(pos=lambda i, v: setattr(rect, 'pos', i.pos),
                   size=lambda i, v: setattr(rect, 'size', i.size))
        lbl = Label(text=self.pair(READY[0], READY[1], 40, 60), font_name=app.font,
                    font_size=sp(40) * app.font_scale, bold=True, color=[1, 1, 1, 1],
                    halign='center', valign='middle')
        lbl.bind(size=lambda i, v: setattr(i, 'text_size', i.size))
        panel.add_widget(lbl)
        self._ft_lbl = lbl
        box.add_widget(panel)
        self._ft_btns = []
        for i, nm in enumerate(self.ft_players):
            b = Factory.StyledButton(text=self.shape(nm, 20, 100) if self.is_ar()
                                     else self.disp_name(nm))
            b.height = dp(90)
            b.bind(on_press=lambda inst, i=i: self.ft_press(i))
            if i in self.ft_out:
                b.disabled = True
            box.add_widget(b)
            self._ft_btns.append(b)
        # (إعادة) جدولة الإشارات إن لم تكن مجدولة، مثلًا بعد تبديل اللغة أثناء الجولة
        if self.ft_state in ('wait', 'go') and not self.ft_events:
            self.ft_state = 'wait'
            self.ft_schedule()

    def ft_schedule(self):
        steps = [READY] + random.sample(FAKES, random.randint(2, 4))
        t = 0.5
        events = []
        for st in steps:
            events.append(Clock.schedule_once(lambda dt, st=st: self.ft_show(st), t))
            t += random.uniform(0.8, 1.7)
        t += random.uniform(0.3, 1.5)
        events.append(Clock.schedule_once(self.ft_real_go, t))
        self.ft_events = events

    def ft_show(self, sig):
        if self.ft_state not in ('wait', 'go') or self._ft_lbl is None:
            return
        self._ft_color.rgba = sig[2]
        self._ft_lbl.text = self.pair(sig[0], sig[1], 40, 60)

    def ft_real_go(self, dt):
        if self.ft_state != 'wait':
            return
        self.ft_state = 'go'
        self.ft_show(REAL)
        self.ft_go_time = time.time()
        self.ft_events.append(Clock.schedule_once(self.ft_timeout, 4.0))

    def ft_timeout(self, dt):
        if self.ft_state == 'go':
            self.ft_end_round(None, None, 'slow')

    def ft_press(self, i):
        if i in self.ft_out:
            return
        if self.ft_state == 'wait':
            self.ft_out.add(i)
            if i < len(self._ft_btns):
                b = self._ft_btns[i]
                b.disabled = True
                b.text = self.fk('out', 18, 100, name=self.disp_name(self.ft_players[i]))
            alive = [k for k in range(len(self.ft_players)) if k not in self.ft_out]
            if len(alive) == 1:
                self.ft_end_round(alive[0], None, 'early')
            elif not alive:
                self.ft_end_round(None, None, 'none')
        elif self.ft_state == 'go':
            ms = int((time.time() - self.ft_go_time) * 1000)
            self.ft_end_round(i, ms, 'ms')

    def ft_end_round(self, winner, ms, reason):
        self.ft_state = 'done'
        self.ft_stop()
        self.ft_last = (winner, ms, reason)
        self.ft_round += 1
        if winner is not None:
            self.ft_scores[winner] += 1
            if self.ft_scores[winner] >= self.ft_target:
                self.go('ft_end')
                return
        self.go('ft_result')

    def show_ft_result(self, box):
        app = App.get_running_app()
        winner, ms, reason = self.ft_last
        if winner is not None:
            box.add_widget(self.label(
                self.fk('wins', 22, 60, name=self.disp_name(self.ft_players[winner])),
                fs=22, bold=True, color=app.primary_color))
            if ms is not None:
                box.add_widget(self.label(self.fk('ms', 16, 60, ms=ms), fs=16))
            elif reason == 'early':
                box.add_widget(self.label(self.fk('early', 16), fs=16))
        else:
            box.add_widget(self.label(self.fk('slow' if reason == 'slow' else 'none', 20), fs=20,
                                      bold=True, color=app.primary_color))
        self.score_lines(box)
        box.add_widget(self.button(self.fk('next', 16, 100), lambda: self.go('ft_ready')))
        box.add_widget(self.button(self.fk('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def show_ft_end(self, box):
        app = App.get_running_app()
        winner = self.ft_last[0]
        box.add_widget(self.label(
            self.fk('champ', 24, 60, name=self.disp_name(self.ft_players[winner])),
            fs=24, bold=True, color=app.primary_color))
        self.score_lines(box, 18)
        box.add_widget(self.button(self.fk('again', 16, 100), self.ft_again))
        box.add_widget(self.button(self.fk('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ft_again(self):
        self.ft_reset()
        self.go('ft_ready')
