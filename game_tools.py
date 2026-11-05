"""أدوات القرار: اختيار عشوائي، نرد، قطعة نقود."""
import random
import re

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

GRAY = [0.45, 0.47, 0.52, 1]

TT = {
    'tl_head': ('Decision tools', 'أدوات القرار'),
    'picker': ('Random picker', 'اختيار عشوائي'),
    'dice': ('Dice', 'نرد'),
    'coin': ('Coin flip', 'قطعة نقود'),
    'pick_hint': ('Write the options, separated by commas or new lines. Example: Pizza, Burger, Sushi',
                  'اكتب الخيارات مفصولة بفواصل أو أسطر. مثال: بيتزا، برغر، سوشي'),
    'pick_ph': ('Pizza, Burger, Sushi', 'بيتزا، برغر، سوشي'),
    'choose': ('Choose for me', 'اختر لي'),
    'pick_need': ('Please enter at least 2 options.', 'الرجاء إدخال خيارين على الأقل.'),
    'dice_n': ('How many dice?', 'كم عدد النرد؟'),
    'roll': ('Roll', 'ارمِ'),
    'total': ('Total: {n}', 'المجموع: {n}'),
    'flip': ('Flip', 'اقلب'),
    'heads': ('Heads', 'صورة'),
    'tails': ('Tails', 'كتابة'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def parse_options(text):
    out = []
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:30]
        if p:
            out.append(p)
    return out[:30]


class ToolsMixin:
    def tools_init(self):
        self.anim = None
        self.pick_result = ''
        self.dice_n = 1
        self.dice_result = []
        self.coin_result = ''
        self._anim_lbl = None

    def stop_anim(self):
        ev = getattr(self, 'anim', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self.anim = None

    def run_anim(self, update, done, ticks=16):
        self.stop_anim()
        state = {'n': 0}

        def tick(dt):
            state['n'] += 1
            if state['n'] >= ticks:
                self.stop_anim()
                done()
                return False
            update()
            return True

        self.anim = Clock.schedule_interval(tick, 0.09)

    def set_anim_text(self, text):
        if self._anim_lbl is not None:
            self._anim_lbl.text = text

    def tl(self, key, fs=16, pad=60, **fmt):
        en, ar = TT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def show_tools_menu(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tl('tl_head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.tl('picker', 17, 100), lambda: self.go('tool_pick')))
        box.add_widget(self.button(self.tl('dice', 17, 100), lambda: self.go('tool_dice')))
        box.add_widget(self.button(self.tl('coin', 17, 100), lambda: self.go('tool_coin')))
        box.add_widget(self.button(self.tl('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def tool_footer(self, box):
        box.add_widget(self.button(self.tl('back', 15, 100), lambda: self.go('tools_menu'),
                                   gray=True))

    def result_label(self, box, text, fs):
        app = App.get_running_app()
        lbl = self.label(text, fs=fs, bold=True, color=app.primary_color)
        box.add_widget(lbl)
        self._anim_lbl = lbl

    # ---------- اختيار عشوائي ----------
    def show_tool_pick(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tl('picker', 20), fs=20, bold=True))
        box.add_widget(self.label(self.tl('pick_hint', 14), fs=14, color=app.muted_color))
        er, _ = self.entry(self.tl('pick_ph', 15, 100), multiline=True, height=dp(110),
                           key='pick_opts')
        box.add_widget(er)
        box.add_widget(self.button(self.tl('choose', 16, 100), self.pick_go))
        self.result_label(box, self.shape(self.pick_result, 30, 60) if self.pick_result else ' ', 30)
        self.tool_footer(box)

    def pick_go(self):
        self.snapshot()
        opts = parse_options(self.form.get('pick_opts', ''))
        if len(opts) < 2:
            self.set_status(self.tl('pick_need', 13))
            return
        self.status = ''
        final = random.choice(opts)

        def done():
            self.pick_result = final
            self.render()

        self.run_anim(lambda: self.set_anim_text(self.shape(random.choice(opts), 30, 60)), done)

    # ---------- نرد ----------
    def show_tool_dice(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tl('dice', 20), fs=20, bold=True))
        box.add_widget(self.label(self.tl('dice_n', 15), fs=15, color=app.muted_color))
        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        for n in (1, 2, 3):
            b = Factory.StyledButton(text=str(n))
            if n != self.dice_n:
                b.custom_bg = GRAY
            b.bind(on_release=lambda inst, n=n: self.dice_set(n))
            row.add_widget(b)
        box.add_widget(row)
        box.add_widget(self.button(self.tl('roll', 16, 100), self.dice_go))
        self.result_label(box, '   '.join(map(str, self.dice_result)) or ' ', 48)
        if len(self.dice_result) > 1:
            box.add_widget(self.label(self.tl('total', 16, 60, n=sum(self.dice_result)), fs=16,
                                      color=app.muted_color))
        self.tool_footer(box)

    def dice_set(self, n):
        self.dice_n = n
        self.dice_result = []
        self.render()

    def dice_go(self):
        n = self.dice_n
        final = [random.randint(1, 6) for _ in range(n)]

        def update():
            self.set_anim_text('   '.join(str(random.randint(1, 6)) for _ in range(n)))

        def done():
            self.dice_result = final
            self.render()

        self.run_anim(update, done)

    # ---------- قطعة نقود ----------
    def show_tool_coin(self, box):
        box.add_widget(self.label(self.tl('coin', 20), fs=20, bold=True))
        box.add_widget(self.button(self.tl('flip', 16, 100), self.coin_go))
        self.result_label(box, self.tl(self.coin_result, 40, 60) if self.coin_result else ' ', 40)
        self.tool_footer(box)

    def coin_go(self):
        final = random.choice(('heads', 'tails'))

        def update():
            self.set_anim_text(self.tl(random.choice(('heads', 'tails')), 40, 60))

        def done():
            self.coin_result = final
            self.render()

        self.run_anim(update, done)
