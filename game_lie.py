"""لعبة «الكذبة والحقيقة»: تكتب عبارتين صحيحتين وكذبة، ويكتشف صديقك الكذبة بكود."""
import base64
import random
import re

from kivy.app import App
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

GRAY = [0.45, 0.47, 0.52, 1]
LIE_VERSION = 1
MAX_NAME = 20
MAX_STMT = 80          # بايت لكل عبارة (نحو 40 حرفًا عربيًا)
_LIE_RE = re.compile(r'BFBL-([A-Z2-7]{1,5}(?:-[A-Z2-7]{1,5})*)', re.IGNORECASE)


def _clip(text, max_bytes):
    b = (text or '').strip().encode('utf-8')[:max_bytes]
    return b.decode('utf-8', errors='ignore')


def _chk(data):
    return (sum(data) * 7 + len(data)) & 0xFF


def encode_lie(name, statements, lie_index):
    if len(statements) != 3 or lie_index not in (0, 1, 2):
        raise ValueError('bad input')
    nm = _clip(name, MAX_NAME).encode('utf-8')
    parts = [_clip(s, MAX_STMT).encode('utf-8') for s in statements]
    if not nm or any(len(p) < 2 for p in parts):
        raise ValueError('empty')
    nonce = random.randrange(256)
    raw = [LIE_VERSION, nonce, (lie_index + nonce) % 3, len(nm)] + [len(p) for p in parts]
    raw += list(nm)
    for p in parts:
        raw += list(p)
    raw.append(_chk(raw))
    text = base64.b32encode(bytes(raw)).decode('ascii').rstrip('=')
    return 'BFBL-' + '-'.join(text[i:i + 5] for i in range(0, len(text), 5))


def decode_lie(text):
    """يرجع {'name', 'statements', 'lie'} أو يرفع ValueError."""
    m = _LIE_RE.search(text or '')
    if not m:
        raise ValueError('no code')
    payload = m.group(1).upper().replace('-', '')
    try:
        raw = list(base64.b32decode(payload + '=' * (-len(payload) % 8)))
    except Exception:
        raise ValueError('bad base32')
    if len(raw) < 9 or _chk(raw[:-1]) != raw[-1] or raw[0] != LIE_VERSION:
        raise ValueError('checksum')
    nonce, enc, nlen = raw[1], raw[2], raw[3]
    lens = raw[4:7]
    if len(raw) != 7 + nlen + sum(lens) + 1:
        raise ValueError('length')
    pos = 7
    try:
        name = bytes(raw[pos:pos + nlen]).decode('utf-8')
        pos += nlen
        stmts = []
        for n in lens:
            stmts.append(bytes(raw[pos:pos + n]).decode('utf-8'))
            pos += n
    except Exception:
        raise ValueError('bad text')
    lie = (enc - nonce) % 3
    return {'name': name, 'statements': stmts, 'lie': lie}


LT = {
    'head': ('Two Truths and a Lie', 'الكذبة والحقيقة'),
    'desc': ('Write 2 true statements and 1 lie about yourself. Your friend has to find the lie.',
             'اكتب عبارتين صحيحتين وكذبة عن نفسك، وعلى صديقك أن يكتشف الكذبة.'),
    'create': ('Create my challenge', 'أنشئ تحديي'),
    'have': ('I received a challenge', 'وصلني تحدٍّ'),
    'name_ph': ('Your name', 'اسمك'),
    'stmt': ('Statement {i}', 'العبارة {i}'),
    'which': ('Which one is the lie?', 'أيها الكذبة؟'),
    'make': ('Create code', 'أنشئ الكود'),
    'need_all': ('Please fill in your name and all three statements.',
                 'الرجاء ملء اسمك والعبارات الثلاث.'),
    'done_head': ('Your challenge is ready!', 'تحديك جاهز!'),
    'done_body': ('Send this code to your friend. They open the app, go to Games and paste it.',
                  'أرسل هذا الكود إلى صديقك. يفتح التطبيق ثم الألعاب ثم يلصقه.'),
    'copy': ('Copy code', 'نسخ الكود'),
    'share': ('Share', 'مشاركة'),
    'paste': ('Paste', 'لصق'),
    'code_head': ('Paste the challenge code', 'الصق كود التحدي'),
    'code_ph': ('BFBL-XXXXX-XXXXX-...', 'BFBL-XXXXX-XXXXX-...'),
    'start': ('Start', 'ابدأ'),
    'bad': ('This code is not valid. Check that you copied all of it.',
            'هذا الكود غير صالح. تأكد أنك نسخته كاملًا.'),
    'says': ('{name} says:', 'يقول {name}:'),
    'ok': ('Correct! You found the lie.', 'صحيح! اكتشفت الكذبة.'),
    'no': ('Wrong! That one was true.', 'خطأ! تلك العبارة كانت حقيقة.'),
    'the_lie': ('The lie was:', 'الكذبة كانت:'),
    'again': ('Try another code', 'جرّب كودًا آخر'),
    'new': ('Create another challenge', 'أنشئ تحديًا آخر'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'share_en': ('Can you spot my lie? Open the BFB app > Games > Two Truths and a Lie > '
                 'I received a challenge, and paste the code below:'),
    'share_ar': ('هل تكتشف كذبتي؟ افتح تطبيق BFB ثم الألعاب ثم الكذبة والحقيقة ثم وصلني تحدٍّ، '
                 'والصق الكود أدناه:'),
}


class LieMixin:
    def lie_init(self):
        self.lie_lie = 0
        self.lie_code = ''
        self.lie_guest = None
        self.lie_pick = None

    def lt(self, key, fs=16, pad=60, **fmt):
        en, ar = LT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def show_lie_home(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.lt('desc', 15), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.lt('create', 16, 100), lambda: self.go('lie_write')))
        box.add_widget(self.button(self.lt('have', 16, 100), lambda: self.go('lie_code')))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def show_lie_write(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('head', 20), fs=20, bold=True, color=app.primary_color))
        row, _ = self.entry(self.lt('name_ph', 16, 100), key='lie_name')
        box.add_widget(row)
        for i in range(3):
            row, _ = self.entry(self.lt('stmt', 15, 100, i=i + 1), key=f'lie_s{i}')
            box.add_widget(row)
        box.add_widget(self.label(self.lt('which', 16), fs=16, bold=True))
        sel = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        for i in range(3):
            b = Factory.StyledButton(text=str(i + 1))
            if i != self.lie_lie:
                b.custom_bg = GRAY
            b.bind(on_release=lambda inst, i=i: self.lie_set(i))
            sel.add_widget(b)
        box.add_widget(sel)
        box.add_widget(self.button(self.lt('make', 16, 100), self.lie_make))
        box.add_widget(self.button(self.lt('back', 15, 100), lambda: self.go('lie_home'), gray=True))

    def lie_set(self, i):
        self.lie_lie = i
        self.render()

    def lie_make(self):
        self.snapshot()
        name = (self.form.get('lie_name') or '').strip()
        stmts = [(self.form.get(f'lie_s{i}') or '').strip() for i in range(3)]
        try:
            self.lie_code = encode_lie(name, stmts, self.lie_lie)
        except ValueError:
            self.set_status(self.lt('need_all', 13))
            return
        self.go('lie_done')

    def show_lie_done(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('done_head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.lt('done_body', 15), fs=15, color=app.muted_color))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.lie_code, fs=13, bold=True))
        box.add_widget(card)
        box.add_widget(self.button(self.lt('copy', 16, 100), lambda: self.do_copy(self.lie_code)))
        box.add_widget(self.button(self.lt('share', 16, 100), self.lie_share))
        box.add_widget(self.button(self.lt('new', 15, 100), lambda: self.go('lie_write'), gray=True))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def lie_share(self):
        text = f"\U0001F382 {LT['share_en'][0]}\n{LT['share_ar'][1]}\n\n{self.lie_code}"
        self.do_share(text)

    def show_lie_code(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('code_head', 20), fs=20, bold=True,
                                  color=app.primary_color))
        row, _ = self.entry(self.lt('code_ph', 14, 100), multiline=True, height=dp(110),
                            key='lie_codetext')
        box.add_widget(row)
        box.add_widget(self.button(self.lt('paste', 15, 100),
                                   lambda: self.paste_into('lie_codetext'), gray=True))
        box.add_widget(self.button(self.lt('start', 16, 100), self.lie_begin))
        box.add_widget(self.button(self.lt('back', 15, 100), lambda: self.go('lie_home'), gray=True))

    def lie_begin(self):
        self.snapshot()
        try:
            self.lie_guest = decode_lie(self.form.get('lie_codetext', ''))
        except ValueError:
            self.set_status(self.lt('bad', 13))
            return
        self.lie_pick = None
        self.go('lie_play')

    def show_lie_play(self, box):
        app = App.get_running_app()
        g = self.lie_guest
        box.add_widget(self.label(self.lt('says', 20, 60, name=self.disp_name(g['name'])),
                                  fs=20, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.lt('which', 16), fs=16, color=app.muted_color))
        for i, s in enumerate(g['statements']):
            box.add_widget(self.button(self.wrap_user(s, 16, 110),
                                       lambda i=i: self.lie_choose(i)))
        box.add_widget(self.button(self.lt('back', 15, 100), lambda: self.go('lie_code'), gray=True))

    def lie_choose(self, i):
        self.lie_pick = i
        self.go('lie_result')

    def show_lie_result(self, box):
        app = App.get_running_app()
        g = self.lie_guest
        ok = self.lie_pick == g['lie']
        from_color = [0.15, 0.62, 0.30, 1] if ok else [0.85, 0.22, 0.25, 1]
        box.add_widget(self.label(self.lt('ok' if ok else 'no', 22), fs=22, bold=True,
                                  color=from_color))
        box.add_widget(self.label(self.lt('the_lie', 15), fs=15, color=app.muted_color))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.wrap_user(g['statements'][g['lie']], 18, 90), fs=18,
                                   bold=True))
        box.add_widget(card)
        box.add_widget(self.button(self.lt('again', 15, 100), lambda: self.go('lie_code')))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))
