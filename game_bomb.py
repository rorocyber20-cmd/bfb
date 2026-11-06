"""لعبة «كود القنبلة»: هاتف واحد، 3 لاعبين فأكثر. أسلاك بعدد اللاعبين + 2، واحد منها يفجّر القنبلة."""
import random
import re

from kivy.app import App
from kivy.clock import Clock

SECONDS = 5
MAX_PLAYERS = 8
RED = [0.85, 0.22, 0.25, 1]
GREEN = [0.15, 0.62, 0.30, 1]

# (إنجليزي، عربي، لون الزر)
WIRES = [
    ('Red', 'أحمر', [0.80, 0.18, 0.20, 1]),
    ('Blue', 'أزرق', [0.15, 0.40, 0.85, 1]),
    ('Green', 'أخضر', [0.15, 0.55, 0.28, 1]),
    ('Orange', 'برتقالي', [0.88, 0.45, 0.08, 1]),
    ('Purple', 'بنفسجي', [0.50, 0.28, 0.72, 1]),
    ('Teal', 'فيروزي', [0.08, 0.50, 0.52, 1]),
    ('Brown', 'بني', [0.45, 0.28, 0.15, 1]),
    ('Pink', 'وردي', [0.80, 0.30, 0.55, 1]),
    ('Gray', 'رمادي', [0.40, 0.42, 0.48, 1]),
    ('Navy', 'كحلي', [0.12, 0.18, 0.42, 1]),
]

BM = {
    'head': ('Bomb Code', 'كود القنبلة'),
    'rules': ('Pass the phone around. The bomb has wires (players + 2) and ONE of them sets it off. '
              'On your turn you have 5 seconds to cut a wire. Cut the wrong one and you are out. '
              'If time runs out, the bomb explodes and you are out. The last player standing wins!',
              'مرّروا الهاتف بينكم. للقنبلة أسلاك (عدد اللاعبين + 2) وواحد منها فقط يفجّرها. '
              'في دورك لديك 5 ثوانٍ لتقطع سلكًا. إن قطعت السلك الخطأ تخرج. '
              'وإن انتهى الوقت تنفجر القنبلة وتخرج. آخر لاعب يبقى يفوز!'),
    'names_hint': ('Enter 3 to 8 player names, separated by commas.',
                   'أدخل من 3 إلى 8 أسماء لاعبين مفصولة بفواصل.'),
    'names_ph': ('Rayan, Mohamed, Bayan', 'ريان ، محمد ، بيان'),
    'need': ('At least 3 different players are needed.', 'يلزم 3 لاعبين مختلفين على الأقل.'),
    'start': ('Start', 'ابدأ'),
    'wires_left': ('Wires: {w}   |   Players: {p}', 'الأسلاك: {w}   |   اللاعبون: {p}'),
    'pass': ('Pass the phone to {name}', 'مرّر الهاتف إلى {name}'),
    'ready': ('I am ready', 'أنا جاهز'),
    'turn': ("{name}: cut a wire!", '{name}: اقطع سلكًا!'),
    'cut': ('Wire cut: {c}', 'السلك المقطوع: {c}'),
    'auto': ("Time's up! The bomb exploded.", 'انتهى الوقت! انفجرت القنبلة.'),
    'safe': ('Safe! {name} survives.', 'نجوت! {name} ما زال في اللعبة.'),
    'boom': ('BOOM! {name} is out!', 'بووم! {name} خرج من اللعبة!'),
    'new_bomb': ('A new bomb is armed with new wires.', 'تم تجهيز قنبلة جديدة بأسلاك جديدة.'),
    'next': ('Next', 'التالي'),
    'winner': ('{name} defused the game and wins!', '{name} هو آخر ناجٍ ويفوز!'),
    'again': ('Play again', 'العب مجددًا'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'back': ('Back', 'رجوع'),
}


def parse_names(text, limit=MAX_PLAYERS):
    out, seen = [], set()
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:14]
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out[:limit]


class BombMixin:
    def bc_init(self):
        self.bc_players = []
        self.bc_alive = []
        self.bc_pos = 0
        self.bc_wires = []        # فهارس الأسلاك المتبقية
        self.bc_bomb = 0
        self.bc_left = SECONDS
        self.bc_ev = None
        self.bc_res = 'safe'
        self.bc_cut_wire = 0
        self.bc_auto = False
        self.bc_fresh = False
        self._bc_lbl = None

    def bc_stop(self):
        ev = getattr(self, 'bc_ev', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self.bc_ev = None

    def bm(self, key, fs=16, pad=60, **fmt):
        en, ar = BM[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def wname(self, i):
        return WIRES[i][1] if self.is_ar() else WIRES[i][0]

    # ---------- الإعداد ----------
    def show_bc_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.bm('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.bm('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.bm('names_hint', 14), fs=14, color=app.muted_color))
        row, _ = self.entry(self.bm('names_ph', 15, 100), key='bc_names')
        box.add_widget(row)
        box.add_widget(self.button(self.bm('start', 16, 100), self.bc_start))
        box.add_widget(self.button(self.bm('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def bc_start(self):
        self.snapshot()
        names = parse_names(self.form.get('bc_names', ''))
        if len(names) < 3:
            self.set_status(self.bm('need', 13))
            return
        self.bc_players = names
        self.bc_reset()
        self.go('bc_pass')

    def bc_reset(self):
        self.bc_alive = list(self.bc_players)
        self.bc_pos = 0
        self.bc_new_bomb()

    def bc_new_bomb(self):
        count = min(len(self.bc_alive) + 2, len(WIRES))
        self.bc_wires = random.sample(range(len(WIRES)), count)
        self.bc_bomb = random.choice(self.bc_wires)

    def bc_name(self):
        return self.disp_name(self.bc_alive[self.bc_pos])

    # ---------- الأدوار ----------
    def show_bc_pass(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.bm('wires_left', 14, 60, w=len(self.bc_wires),
                                          p=len(self.bc_alive)), fs=14, color=app.muted_color))
        if self.bc_fresh:
            box.add_widget(self.label(self.bm('new_bomb', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.bm('pass', 24, 60, name=self.bc_name()), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.bm('ready', 17, 100), self.bc_ready))

    def bc_ready(self):
        self.bc_left = SECONDS
        self.bc_fresh = False
        self.go('bc_turn')

    def show_bc_turn(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.bm('turn', 20, 60, name=self.bc_name()), fs=20, bold=True,
                                  color=app.primary_color))
        timer = self.label(str(max(0, self.bc_left)), fs=48, bold=True,
                           color=RED if self.bc_left <= 2 else app.text_color)
        box.add_widget(timer)
        self._bc_lbl = timer
        for wi in self.bc_wires:
            b = self.button(self.wname(wi), lambda wi=wi: self.bc_cut(wi))
            b.custom_bg = WIRES[wi][2]
            box.add_widget(b)
        if self.bc_left > 0:
            self.bc_ev = Clock.schedule_interval(self.bc_tick, 1.0)

    def bc_tick(self, dt):
        self.bc_left -= 1
        if self._bc_lbl is not None:
            self._bc_lbl.text = str(max(0, self.bc_left))
            if self.bc_left <= 2:
                self._bc_lbl.color = RED
        if self.bc_left <= 0:
            self.bc_stop()
            self.bc_cut(self.bc_bomb, auto=True)     # انتهى الوقت = انفجار
            return False
        return True

    def bc_cut(self, wi, auto=False):
        self.bc_stop()
        self.bc_cut_wire = wi
        self.bc_auto = auto
        if wi == self.bc_bomb:
            self.bc_res = 'boom'
        else:
            self.bc_res = 'safe'
            self.bc_wires.remove(wi)
        self.go('bc_res')

    def show_bc_res(self, box):
        app = App.get_running_app()
        name = self.bc_name()
        if self.bc_auto:
            box.add_widget(self.label(self.bm('auto', 16), fs=16, color=app.muted_color))
        else:
            box.add_widget(self.label(self.bm('cut', 16, 60, c=self.wname(self.bc_cut_wire)),
                                      fs=16, color=app.muted_color))
        if self.bc_res == 'boom':
            box.add_widget(self.label(self.bm('boom', 28, 60, name=name), fs=28, bold=True,
                                      color=RED))
        else:
            box.add_widget(self.label(self.bm('safe', 24, 60, name=name), fs=24, bold=True,
                                      color=GREEN))
        box.add_widget(self.button(self.bm('next', 16, 100), self.bc_next))

    def bc_next(self):
        if self.bc_res == 'boom':
            self.bc_alive.pop(self.bc_pos)
            if len(self.bc_alive) <= 1:
                self.go('bc_end')
                return
            self.bc_pos %= len(self.bc_alive)
            self.bc_new_bomb()
            self.bc_fresh = True
        else:
            self.bc_pos = (self.bc_pos + 1) % len(self.bc_alive)
        self.go('bc_pass')

    def show_bc_end(self, box):
        app = App.get_running_app()
        name = self.disp_name(self.bc_alive[0]) if self.bc_alive else ''
        box.add_widget(self.label(self.bm('winner', 24, 60, name=name), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.bm('again', 16, 100), self.bc_again))
        box.add_widget(self.button(self.bm('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def bc_again(self):
        self.bc_reset()
        self.go('bc_pass')
