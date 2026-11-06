"""أدوات القرار: اختيار عشوائي، نرد، قطعة نقود."""
import math
import random
import re

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Mesh, PopMatrix, PushMatrix, Rotate, Triangle
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

GRAY = [0.45, 0.47, 0.52, 1]

TT = {
    'tl_head': ('Decision tools', 'أدوات القرار'),
    'picker': ('Random picker', 'اختيار عشوائي'),
    'wheel': ('Wheel', 'عجلة'),
    'coin': ('Coin flip', 'قطعة نقود'),
    'pick_hint': ('Write the options, separated by commas or new lines. Example: Pizza, Burger, Sushi',
                  'اكتب الخيارات مفصولة بفواصل أو أسطر. مثال: بيتزا، برغر، سوشي'),
    'pick_ph': ('Pizza, Burger, Sushi', 'بيتزا، برغر، سوشي'),
    'choose': ('Choose for me', 'اختر لي'),
    'pick_need': ('Please enter at least 2 options.', 'الرجاء إدخال خيارين على الأقل.'),
    'wheel_hint': ('Write 2 to 12 options, separated by commas or new lines.',
                   'اكتب من 2 إلى 12 خيارًا مفصولة بفواصل أو أسطر.'),
    'wheel_ph': ('Pizza, Burger, Sushi', 'بيتزا، برغر، سوشي'),
    'spin': ('Spin the wheel', 'أدِر العجلة'),
    'wheel_need': ('Please enter between 2 and 12 options.', 'الرجاء إدخال من 2 إلى 12 خيارًا.'),
    'flip': ('Flip', 'اقلب'),
    'heads': ('Heads', 'صورة'),
    'tails': ('Tails', 'كتابة'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def parse_options(text, limit=30):
    out = []
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:30]
        if p:
            out.append(p)
    return out[:limit]


WHEEL_COLORS = [
    (0.90, 0.30, 0.30, 1), (0.95, 0.60, 0.20, 1), (0.95, 0.80, 0.25, 1), (0.45, 0.75, 0.35, 1),
    (0.20, 0.70, 0.65, 1), (0.25, 0.55, 0.90, 1), (0.45, 0.40, 0.85, 1), (0.75, 0.40, 0.80, 1),
    (0.90, 0.40, 0.65, 1), (0.55, 0.55, 0.60, 1), (0.65, 0.45, 0.30, 1), (0.30, 0.45, 0.55, 1),
]


class WheelWidget(Widget):
    """عجلة ملوّنة. الزاوية angle تدور عكس عقارب الساعة، والمؤشر ثابت في الأعلى.
    الشريحة i تمتد من i*seg إلى (i+1)*seg مقيسة مع عقارب الساعة من الأعلى،
    فالفائز عند زاوية a هو: floor((a % 360) / seg)."""
    angle = NumericProperty(0)
    n = NumericProperty(2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, angle=self.redraw, n=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        n = max(2, int(self.n))
        cx, cy = self.center
        r = min(self.width, self.height) / 2 - dp(18)
        if r <= 0:
            return
        seg = 360.0 / n
        with self.canvas:
            PushMatrix()
            Rotate(angle=self.angle, origin=(cx, cy))
            for i in range(n):
                Color(*WHEEL_COLORS[i % len(WHEEL_COLORS)])
                steps = max(2, int(seg / 6) + 1)
                verts = [cx, cy, 0, 0]
                for k in range(steps + 1):
                    phi = math.radians(i * seg + seg * k / steps)
                    verts += [cx + r * math.sin(phi), cy + r * math.cos(phi), 0, 0]
                Mesh(vertices=verts, indices=list(range(len(verts) // 4)), mode='triangle_fan')
            PopMatrix()
            Color(0.15, 0.15, 0.18, 1)
            Ellipse(pos=(cx - dp(9), cy - dp(9)), size=(dp(18), dp(18)))
            Triangle(points=[cx - dp(13), cy + r + dp(16), cx + dp(13), cy + r + dp(16),
                             cx, cy + r - dp(8)])


class ToolsMixin:
    def tools_init(self):
        self.anim = None
        self.pick_result = ''
        self.wheel_opts = []
        self.wheel_result = ''
        self.wheel_angle = 0.0
        self.wheel_anim = None
        self._wheel = None
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
        wa = getattr(self, 'wheel_anim', None)
        if wa is not None:
            try:
                wa.cancel(self._wheel)
            except Exception:
                pass
        self.wheel_anim = None

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
        box.add_widget(self.button(self.tl('wheel', 17, 100), lambda: self.go('tool_wheel')))
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

    # ---------- عجلة ----------
    def show_tool_wheel(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tl('wheel', 20), fs=20, bold=True))
        box.add_widget(self.label(self.tl('wheel_hint', 14), fs=14, color=app.muted_color))
        er, _ = self.entry(self.tl('wheel_ph', 15, 100), multiline=True, height=dp(110),
                           key='wheel_opts')
        box.add_widget(er)
        box.add_widget(self.button(self.tl('spin', 16, 100), self.wheel_go))
        wheel = WheelWidget(size_hint_y=None, height=dp(300))
        wheel.n = max(2, len(self.wheel_opts))
        wheel.angle = self.wheel_angle
        self._wheel = wheel
        box.add_widget(wheel)
        self.result_label(box, self.shape(self.wheel_result, 30, 60) if self.wheel_result else ' ', 30)
        for i, opt in enumerate(self.wheel_opts):
            row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(10))
            sw = Widget(size_hint_x=None, width=dp(22))
            col = WHEEL_COLORS[i % len(WHEEL_COLORS)]
            with sw.canvas:
                Color(*col)
                rect = Triangle(points=[0, 0, 0, 0, 0, 0])
            row.add_widget(sw)
            row.add_widget(self.label(self.shape(opt, 15, 100), fs=15, halign='left'))
            box.add_widget(row)
            self._color_swatch(sw, rect)
        self.tool_footer(box)

    def _color_swatch(self, sw, tri):
        def upd(*a):
            x, y = sw.pos
            w, h = sw.size
            tri.points = [x, y + h * 0.15, x + w, y + h * 0.15, x + w / 2, y + h * 0.85]
        sw.bind(pos=upd, size=upd)
        upd()

    def wheel_go(self):
        self.snapshot()
        opts = parse_options(self.form.get('wheel_opts', ''), limit=12)
        if len(opts) < 2:
            self.set_status(self.tl('wheel_need', 13))
            return
        self.status = ''
        self.wheel_opts = opts
        self.wheel_result = ''
        self.render()                      # يبني العجلة والأسماء الجديدة
        wheel = self._wheel
        seg = 360.0 / len(opts)
        idx = random.randrange(len(opts))
        theta = (idx + random.uniform(0.15, 0.85)) * seg
        cur = wheel.angle
        final = cur - (cur % 360) + 360 * 5 + theta
        anim = Animation(angle=final, duration=3.5, t='out_cubic')

        def finished(*a):
            self.wheel_angle = final % 360
            self.wheel_result = opts[idx]
            self.wheel_anim = None
            self.render()

        anim.bind(on_complete=finished)
        self.wheel_anim = anim
        anim.start(wheel)

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
