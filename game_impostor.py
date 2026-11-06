"""لعبة «المحتال»: هاتف واحد يمر بين اللاعبين؛ واحد منهم يأخذ كلمة قريبة من كلمة الباقين."""
import random
import re

from kivy.app import App
from kivy.factory import Factory

# (كلمة اللاعبين، الكلمة القريبة للمحتال) — كل كلمة (إنجليزي، عربي)
WORD_PAIRS = [
    (('Lion', 'أسد'), ('Tiger', 'نمر')),
    (('Coffee', 'قهوة'), ('Tea', 'شاي')),
    (('Cat', 'قطة'), ('Dog', 'كلب')),
    (('Beach', 'شاطئ'), ('Swimming pool', 'مسبح')),
    (('Football', 'كرة القدم'), ('Basketball', 'كرة السلة')),
    (('Doctor', 'طبيب'), ('Nurse', 'ممرض')),
    (('Apple', 'تفاحة'), ('Orange', 'برتقالة')),
    (('Car', 'سيارة'), ('Bus', 'حافلة')),
    (('Moon', 'قمر'), ('Sun', 'شمس')),
    (('Mountain', 'جبل'), ('Hill', 'تلة')),
    (('Rain', 'مطر'), ('Snow', 'ثلج')),
    (('Guitar', 'غيتار'), ('Piano', 'بيانو')),
    (('Bread', 'خبز'), ('Cake', 'كعكة')),
    (('Pen', 'قلم حبر'), ('Pencil', 'قلم رصاص')),
    (('School', 'مدرسة'), ('University', 'جامعة')),
    (('River', 'نهر'), ('Sea', 'بحر')),
    (('Airplane', 'طائرة'), ('Helicopter', 'مروحية')),
    (('Watch', 'ساعة يد'), ('Wall clock', 'ساعة حائط')),
    (('Chocolate', 'شوكولاتة'), ('Candy', 'حلوى')),
    (('Mosque', 'مسجد'), ('Library', 'مكتبة')),
    (('Pizza', 'بيتزا'), ('Burger', 'برغر')),
    (('Train', 'قطار'), ('Tram', 'ترامواي')),
    (('Wedding', 'عرس'), ('Birthday party', 'حفلة عيد ميلاد')),
    (('Desert', 'صحراء'), ('Forest', 'غابة')),
    (('Phone', 'هاتف'), ('Tablet', 'لوح إلكتروني')),
]

IT = {
    'head': ('The Impostor', 'المحتال'),
    'desc': ('Everyone gets the same word, except one player who gets a similar word. '
             'Talk about the word without saying it and find the impostor!',
             'يأخذ الجميع نفس الكلمة، ما عدا لاعب واحد يأخذ كلمة قريبة منها. '
             'تحدثوا عن الكلمة دون ذكرها واكتشفوا المحتال!'),
    'names_hint': ('Enter 3 to 8 player names, separated by commas.',
                   'أدخل من 3 إلى 8 أسماء لاعبين مفصولة بفواصل.'),
    'names_ph': ('Rayan, Mohamed, Bayan', 'ريان ، محمد ، بيان'),
    'need': ('At least 3 players are needed.', 'يلزم 3 لاعبين على الأقل.'),
    'start': ('Start', 'ابدأ'),
    'pass': ('Pass the phone to {name}', 'مرّر الهاتف إلى {name}'),
    'show': ('Show my word', 'أرني كلمتي'),
    'your_word': ('Your word is:', 'كلمتك هي:'),
    'hide': ('Hide and pass the phone', 'أخفِ الكلمة ومرّر الهاتف'),
    'last': ('Hide and continue', 'أخفِ الكلمة وتابع'),
    'talk_head': ('Discussion time!', 'وقت النقاش!'),
    'talk_body': ('Each player describes the word with one sentence, without saying it. '
                  '{name} starts. Then vote for the impostor.',
                  'يصف كل لاعب الكلمة بجملة واحدة دون ذكرها. يبدأ {name}. ثم صوّتوا على المحتال.'),
    'reveal': ('Reveal the impostor', 'اكشف المحتال'),
    'imp_was': ('The impostor was {name}', 'المحتال كان {name}'),
    'words': ('Everyone had: {a}', 'كلمة الجميع: {a}'),
    'imp_word': ('The impostor had: {b}', 'كلمة المحتال: {b}'),
    'again': ('Play again', 'العب مجددًا'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def parse_names(text, limit=8):
    out, seen = [], set()
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:14]
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out[:limit]


class ImpostorMixin:
    def imp_init(self):
        self.imp_players = []
        self.imp_i = 0
        self.imp_show = False
        self.imp_pair = None
        self.imp_who = 0
        self.imp_first = 0

    def it(self, key, fs=16, pad=60, **fmt):
        en, ar = IT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def raw(self, w):
        return w[1] if self.is_ar() else w[0]

    def show_imp_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.it('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.it('desc', 15), fs=15, color=app.muted_color))
        box.add_widget(self.label(self.it('names_hint', 14), fs=14, color=app.muted_color))
        row, _ = self.entry(self.it('names_ph', 15, 100), key='imp_names')
        box.add_widget(row)
        box.add_widget(self.button(self.it('start', 16, 100), self.imp_start))
        box.add_widget(self.button(self.it('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def imp_start(self):
        self.snapshot()
        names = parse_names(self.form.get('imp_names', ''))
        if len(names) < 3:
            self.set_status(self.it('need', 13))
            return
        self.imp_players = names
        self.imp_new_round()
        self.go('imp_turn')

    def imp_new_round(self):
        self.imp_pair = random.choice(WORD_PAIRS)
        self.imp_who = random.randrange(len(self.imp_players))
        self.imp_first = random.randrange(len(self.imp_players))
        self.imp_i = 0
        self.imp_show = False

    def show_imp_turn(self, box):
        app = App.get_running_app()
        name = self.disp_name(self.imp_players[self.imp_i])
        if not self.imp_show:
            box.add_widget(self.label(self.it('pass', 22, 60, name=name), fs=22, bold=True,
                                      color=app.primary_color))
            box.add_widget(self.button(self.it('show', 17, 100), self.imp_reveal_word))
        else:
            word = self.imp_pair[1] if self.imp_i == self.imp_who else self.imp_pair[0]
            box.add_widget(self.label(self.it('your_word', 16), fs=16, color=app.muted_color))
            card = Factory.GiftCard()
            card.add_widget(self.label(self.shape(self.raw(word), 30, 60), fs=30, bold=True,
                                       color=app.primary_color))
            box.add_widget(card)
            last = self.imp_i + 1 >= len(self.imp_players)
            box.add_widget(self.button(self.it('last' if last else 'hide', 16, 100),
                                       self.imp_next))

    def imp_reveal_word(self):
        self.imp_show = True
        self.render()

    def imp_next(self):
        self.imp_show = False
        self.imp_i += 1
        if self.imp_i >= len(self.imp_players):
            self.go('imp_talk')
        else:
            self.render()

    def show_imp_talk(self, box):
        app = App.get_running_app()
        first = self.disp_name(self.imp_players[self.imp_first])
        box.add_widget(self.label(self.it('talk_head', 24), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.it('talk_body', 17, 60, name=first), fs=17))
        box.add_widget(self.button(self.it('reveal', 16, 100), lambda: self.go('imp_reveal')))

    def show_imp_reveal(self, box):
        app = App.get_running_app()
        who = self.disp_name(self.imp_players[self.imp_who])
        box.add_widget(self.label(self.it('imp_was', 24, 60, name=who), fs=24, bold=True,
                                  color=app.primary_color))
        a = self.raw(self.imp_pair[0])
        b = self.raw(self.imp_pair[1])
        box.add_widget(self.label(self.it('words', 18, 60, a=a), fs=18))
        box.add_widget(self.label(self.it('imp_word', 18, 60, b=b), fs=18))
        box.add_widget(self.button(self.it('again', 16, 100), self.imp_again))
        box.add_widget(self.button(self.it('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def imp_again(self):
        self.imp_new_round()
        self.go('imp_turn')
