"""لعبة «الكذبة والحقيقة»: تكتب عبارتين صحيحتين وكذبة، ويكتشف صديقك الكذبة بكود."""
import base64
import random
import re

from kivy.app import App
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout


GRAY = [0.45, 0.47, 0.52, 1]
LIE_VERSION = 2
MAX_NAME = 20
MAX_STMT = 60          # بايت لكل عبارة (نحو 30 حرفًا عربيًا أو 60 إنجليزيًا)
MAX_ROUNDS = 5
_LIE_RE = re.compile(r'BFBL-([A-Z2-7]{1,5}(?:-[A-Z2-7]{1,5})*)', re.IGNORECASE)


def _clip(text, max_bytes):
    b = (text or '').strip().encode('utf-8')[:max_bytes]
    return b.decode('utf-8', errors='ignore')


def _chk(data):
    return (sum(data) * 7 + len(data)) & 0xFF


def encode_lie(name, rounds):
    """rounds: قائمة (عبارات [3]، رقم الكذبة 0..2) من 1 إلى 5 جولات."""
    if not 1 <= len(rounds) <= MAX_ROUNDS:
        raise ValueError('rounds')
    nm = _clip(name, MAX_NAME).encode('utf-8')
    if not nm:
        raise ValueError('empty name')
    nonce = random.randrange(256)
    meta, texts = [], []
    for r, (stmts, lie) in enumerate(rounds):
        if len(stmts) != 3 or lie not in (0, 1, 2):
            raise ValueError('bad round')
        parts = [_clip(x, MAX_STMT).encode('utf-8') for x in stmts]
        if any(len(p) < 2 for p in parts):
            raise ValueError('empty statement')
        meta += [(lie + nonce + r) % 3] + [len(p) for p in parts]
        for p in parts:
            texts += list(p)
    raw = [LIE_VERSION, nonce, len(rounds), len(nm)] + meta + list(nm) + texts
    raw.append(_chk(raw))
    text = base64.b32encode(bytes(raw)).decode('ascii').rstrip('=')
    return 'BFBL-' + '-'.join(text[i:i + 5] for i in range(0, len(text), 5))


def _decode_v1(raw):
    nonce, enc, nlen = raw[1], raw[2], raw[3]
    lens = raw[4:7]
    if len(raw) != 7 + nlen + sum(lens) + 1:
        raise ValueError('length')
    pos = 7 + nlen
    name = bytes(raw[7:pos]).decode('utf-8')
    stmts = []
    for n in lens:
        stmts.append(bytes(raw[pos:pos + n]).decode('utf-8'))
        pos += n
    return {'name': name, 'rounds': [{'statements': stmts, 'lie': (enc - nonce) % 3}]}


def decode_lie(text):
    """يرجع {'name', 'rounds': [{'statements', 'lie'}]} أو يرفع ValueError."""
    m = _LIE_RE.search(text or '')
    if not m:
        raise ValueError('no code')
    payload = m.group(1).upper().replace('-', '')
    try:
        raw = list(base64.b32decode(payload + '=' * (-len(payload) % 8)))
    except Exception:
        raise ValueError('bad base32')
    if len(raw) < 9 or _chk(raw[:-1]) != raw[-1]:
        raise ValueError('checksum')
    try:
        if raw[0] == 1:
            return _decode_v1(raw)
        if raw[0] != LIE_VERSION:
            raise ValueError('version')
        nonce, nr, nlen = raw[1], raw[2], raw[3]
        if not 1 <= nr <= MAX_ROUNDS:
            raise ValueError('rounds')
        meta = raw[4:4 + 4 * nr]
        total = sum(meta[i] for i in range(len(meta)) if i % 4)
        if len(raw) != 4 + 4 * nr + nlen + total + 1:
            raise ValueError('length')
        pos = 4 + 4 * nr
        name = bytes(raw[pos:pos + nlen]).decode('utf-8')
        pos += nlen
        rounds = []
        for r in range(nr):
            enc, lens = meta[4 * r], meta[4 * r + 1:4 * r + 4]
            stmts = []
            for n in lens:
                stmts.append(bytes(raw[pos:pos + n]).decode('utf-8'))
                pos += n
            rounds.append({'statements': stmts, 'lie': (enc - nonce - r) % 3})
        return {'name': name, 'rounds': rounds}
    except ValueError:
        raise
    except Exception:
        raise ValueError('bad text')


LT = {
    'head': ('Two Truths and a Lie', 'الكذبة والحقيقة'),
    'desc': ('Write 2 true statements and 1 lie about yourself, in 1, 3 or 5 rounds. '
             'Your friend has to find the lie each time. Play on one phone or send a code.',
             'اكتب عبارتين صحيحتين وكذبة عن نفسك في جولة أو 3 أو 5 جولات، وعلى صديقك اكتشاف الكذبة في كل مرة. '
             'العبوها على هاتف واحد أو أرسلوا كودًا.'),
    'create': ('Create my challenge', 'أنشئ تحديي'),
    'have': ('I received a challenge', 'وصلني تحدٍّ'),
    'name_ph': ('Your name', 'اسمك'),
    'rounds_head': ('How many rounds?', 'كم عدد الجولات؟'),
    'rounds_hint': ('Each round has 2 truths and 1 lie.', 'في كل جولة حقيقتان وكذبة.'),
    'cont': ('Continue', 'متابعة'),
    'need_name': ('Please enter your name.', 'الرجاء إدخال اسمك.'),
    'round_of': ('Round {i} of {n}', 'الجولة {i} من {n}'),
    'stmt': ('Statement {i}', 'العبارة {i}'),
    'which': ('Which one is the lie?', 'أيها الكذبة؟'),
    'next_round': ('Next round', 'الجولة التالية'),
    'make': ('Create code', 'أنشئ الكود'),
    'need_all': ('Please fill in all three statements (at least 2 letters each).',
                 'الرجاء ملء العبارات الثلاث (حرفان على الأقل لكل واحدة).'),
    'done_head': ('Your challenge is ready!', 'تحديك جاهز!'),
    'done_body': ('Play it now on this phone, or send the code to a friend. '
                  'They open the app, go to Games and paste it.',
                  'العبه الآن على هذا الهاتف، أو أرسل الكود إلى صديقك. '
                  'يفتح التطبيق ثم الألعاب ثم يلصقه.'),
    'play_here': ('Play on this phone', 'العب على هذا الهاتف'),
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
    'next': ('Next', 'التالي'),
    'see': ('See my score', 'اعرض نتيجتي'),
    'score_head': ('Your score', 'نتيجتك'),
    'again': ('Try another code', 'جرّب كودًا آخر'),
    'played': ('You already played this challenge. Ask your friend for a new one.',
               'لعبت هذا التحدي من قبل. اطلب من صديقك تحديًا جديدًا.'),
    'new': ('Create another challenge', 'أنشئ تحديًا آخر'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'share_en': ('Can you spot my lies? Open the BFB app > Games > Two Truths and a Lie > '
                 'I received a challenge, and paste the code below:'),
    'share_ar': ('هل تكتشف كذباتي؟ افتح تطبيق BFB ثم الألعاب ثم الكذبة والحقيقة ثم وصلني تحدٍّ، '
                 'والصق الكود أدناه:'),
}

OK_COLOR = [0.15, 0.62, 0.30, 1]
BAD_COLOR = [0.85, 0.22, 0.25, 1]


class LieMixin:
    def lie_init(self):
        self.lie_n = 1
        self.lie_lie = 0
        self.lie_ri = 0
        self.lie_rounds = []
        self.lie_name = ''
        self.lie_code = ''
        self.lie_guest = None
        self.lie_pick = None
        self.lie_score = 0

    def lt(self, key, fs=16, pad=60, **fmt):
        en, ar = LT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def clear_lie_fields(self):
        for i in range(3):
            self.form.pop(f'lie_s{i}', None)
        self.lie_lie = 0

    # ---------- الصفحة الأولى والإعداد ----------
    def show_lie_home(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.lt('desc', 15), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.lt('create', 16, 100), lambda: self.go('lie_setup')))
        box.add_widget(self.button(self.lt('have', 16, 100), lambda: self.go('lie_code')))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def show_lie_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('head', 20), fs=20, bold=True, color=app.primary_color))
        row, _ = self.entry(self.lt('name_ph', 16, 100), key='lie_name')
        box.add_widget(row)
        box.add_widget(self.label(self.lt('rounds_head', 16), fs=16, bold=True))
        box.add_widget(self.label(self.lt('rounds_hint', 13), fs=13, color=app.muted_color))
        sel = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        for n in (1, 3, 5):
            b = Factory.StyledButton(text=str(n))
            if n != self.lie_n:
                b.custom_bg = GRAY
            b.bind(on_release=lambda inst, n=n: self.lie_set_n(n))
            sel.add_widget(b)
        box.add_widget(sel)
        box.add_widget(self.button(self.lt('cont', 16, 100), self.lie_setup_next))
        box.add_widget(self.button(self.lt('back', 15, 100), lambda: self.go('lie_home'), gray=True))

    def lie_set_n(self, n):
        self.lie_n = n
        self.render()

    def lie_setup_next(self):
        self.snapshot()
        name = (self.form.get('lie_name') or '').strip()
        if not name:
            self.set_status(self.lt('need_name', 13))
            return
        self.lie_name = name
        self.lie_rounds = []
        self.lie_ri = 0
        self.clear_lie_fields()
        self.go('lie_write')

    # ---------- كتابة الجولات ----------
    def show_lie_write(self, box):
        app = App.get_running_app()
        if self.lie_n > 1:
            box.add_widget(self.label(self.lt('round_of', 20, 60, i=self.lie_ri + 1, n=self.lie_n),
                                      fs=20, bold=True, color=app.primary_color))
        else:
            box.add_widget(self.label(self.lt('head', 20), fs=20, bold=True,
                                      color=app.primary_color))
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
        last = self.lie_ri + 1 >= self.lie_n
        box.add_widget(self.button(self.lt('make' if last else 'next_round', 16, 100),
                                   self.lie_make))
        box.add_widget(self.button(self.lt('back', 15, 100), lambda: self.go('lie_setup'),
                                   gray=True))

    def lie_set(self, i):
        self.lie_lie = i
        self.render()

    def lie_make(self):
        self.snapshot()
        stmts = [(self.form.get(f'lie_s{i}') or '').strip() for i in range(3)]
        if any(len(x) < 2 for x in stmts):
            self.set_status(self.lt('need_all', 13))
            return
        self.lie_rounds.append((stmts, self.lie_lie))
        if self.lie_ri + 1 < self.lie_n:
            self.lie_ri += 1
            self.clear_lie_fields()
            for ti in self._tis.values():
                ti.text = ''
            self.status = ''
            self.render()
            return
        try:
            self.lie_code = encode_lie(self.lie_name, self.lie_rounds)
        except ValueError:
            self.lie_rounds.pop()
            self.set_status(self.lt('need_all', 13))
            return
        self.go('lie_done')

    def show_lie_done(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.lt('done_head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.lt('done_body', 15), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.lt('play_here', 16, 100), self.lie_play_here))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.lie_code, fs=12, bold=True))
        box.add_widget(card)
        box.add_widget(self.button(self.lt('copy', 16, 100), lambda: self.do_copy(self.lie_code)))
        box.add_widget(self.button(self.lt('share', 16, 100), self.lie_share))
        box.add_widget(self.button(self.lt('new', 15, 100), lambda: self.go('lie_setup'), gray=True))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def lie_play_here(self):
        self.lie_guest = {'name': self.lie_name,
                          'rounds': [{'statements': s, 'lie': l} for s, l in self.lie_rounds]}
        self.lie_start_play()

    def lie_share(self):
        text = f"\U0001F382 {LT['share_en'][0]}\n{LT['share_ar'][1]}\n\n{self.lie_code}"
        self.do_share(text)

    # ---------- اللعب ----------
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
        # فرصة واحدة لكل تحدٍّ
        m = _LIE_RE.search(self.form.get('lie_codetext', ''))
        if not self.claim_code('lie', m.group(1)):
            self.set_status(self.lt('played', 13))
            return
        self.lie_start_play()

    def lie_start_play(self):
        self.lie_ri = 0
        self.lie_score = 0
        self.lie_pick = None
        self.go('lie_play')

    def show_lie_play(self, box):
        app = App.get_running_app()
        g = self.lie_guest
        n = len(g['rounds'])
        if n > 1:
            box.add_widget(self.label(self.lt('round_of', 14, 60, i=self.lie_ri + 1, n=n), fs=14,
                                      color=app.muted_color))
        box.add_widget(self.label(self.lt('says', 20, 60, name=self.disp_name(g['name'])),
                                  fs=20, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.lt('which', 16), fs=16, color=app.muted_color))
        rd = g['rounds'][self.lie_ri]
        for i, s in enumerate(rd['statements']):
            box.add_widget(self.button(self.wrap_user(s, 16, 110),
                                       lambda i=i: self.lie_choose(i)))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def lie_choose(self, i):
        self.lie_pick = i
        if i == self.lie_guest['rounds'][self.lie_ri]['lie']:
            self.lie_score += 1
        self.go('lie_fb')

    def show_lie_fb(self, box):
        app = App.get_running_app()
        g = self.lie_guest
        n = len(g['rounds'])
        rd = g['rounds'][self.lie_ri]
        ok = self.lie_pick == rd['lie']
        box.add_widget(self.label(self.lt('ok' if ok else 'no', 22), fs=22, bold=True,
                                  color=OK_COLOR if ok else BAD_COLOR))
        box.add_widget(self.label(self.lt('the_lie', 15), fs=15, color=app.muted_color))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.wrap_user(rd['statements'][rd['lie']], 18, 90), fs=18,
                                   bold=True))
        box.add_widget(card)
        if self.lie_ri + 1 < n:
            box.add_widget(self.button(self.lt('next', 16, 100), self.lie_next))
        elif n > 1:
            box.add_widget(self.button(self.lt('see', 16, 100), lambda: self.go('lie_end')))
        else:
            box.add_widget(self.button(self.lt('again', 15, 100), lambda: self.go('lie_code')))
            box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'),
                                       gray=True))

    def lie_next(self):
        self.lie_ri += 1
        self.lie_pick = None
        self.go('lie_play')

    def show_lie_end(self, box):
        app = App.get_running_app()
        n = len(self.lie_guest['rounds'])
        box.add_widget(self.label(self.lt('score_head', 16), fs=16, color=app.muted_color))
        box.add_widget(self.label(f"{self.lie_score} / {n}", fs=44, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.lt('again', 15, 100), lambda: self.go('lie_code'),
                                   gray=True))
        box.add_widget(self.button(self.lt('menu', 15, 100), lambda: self.go('menu'), gray=True))
