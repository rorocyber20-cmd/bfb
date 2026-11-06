"""ألعاب العقل: ثقافة عامة (10 أسئلة ونقاط) وألغاز."""
import os
import random

from kivy.app import App
from kivy.factory import Factory

import brain_data as bd
import core

BEST_FILE = os.path.join(core.data_dir(), 'trivia_best.json')
GREEN = [0.15, 0.62, 0.30, 1]
RED = [0.85, 0.22, 0.25, 1]
N_Q = 10

BT = {
    'tv_head': ('General Knowledge', 'ثقافة عامة'),
    'tv_desc': ('10 random questions. Try to beat your best score!',
                '10 أسئلة عشوائية. حاول أن تتجاوز أفضل نتيجة لك!'),
    'best': ('Best score: {n} / {t}', 'أفضل نتيجة: {n} / {t}'),
    'start': ('Start', 'ابدأ'),
    'progress': ('Question {i} of {n}', 'السؤال {i} من {n}'),
    'right': ('Correct!', 'إجابة صحيحة!'),
    'wrong': ('Wrong!', 'إجابة خاطئة!'),
    'ans': ('Correct answer: {a}', 'الإجابة الصحيحة: {a}'),
    'next': ('Next', 'التالي'),
    'finish': ('See my score', 'اعرض نتيجتي'),
    'score_head': ('Your score', 'نتيجتك'),
    'new_best': ('New best score!', 'رقم قياسي جديد!'),
    'again': ('Play again', 'العب مجددًا'),
    'rd_head': ('Riddles', 'ألغاز'),
    'rd_desc': ('Think! Use the hint if you are stuck, then reveal the answer.',
                'فكّر! استعمل التلميح إن احترت، ثم اكشف الجواب.'),
    'hint': ('Hint', 'تلميح'),
    'answer': ('Show answer', 'اعرض الجواب'),
    'next_r': ('Next riddle', 'لغز آخر'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


class BrainMixin:
    def brain_init(self):
        self.tv_qs = []
        self.tv_i = 0
        self.tv_score = 0
        self.tv_opts = []
        self.tv_pick = None
        self.tv_new_best = False
        self.rd_deck = []
        self.rd_cur = None
        self.rd_hint = False
        self.rd_ans = False

    def bt(self, key, fs=16, pad=60, **fmt):
        en, ar = BT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def raw2(self, en, ar):
        return ar if self.is_ar() else en

    # ---------- ثقافة عامة ----------
    def tv_best(self):
        data = core._read(BEST_FILE, {})
        return int(data.get('best', 0)) if isinstance(data, dict) else 0

    def show_tv_home(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.bt('tv_head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.bt('tv_desc', 15), fs=15, color=app.muted_color))
        best = self.tv_best()
        if best:
            box.add_widget(self.label(self.bt('best', 16, 60, n=best, t=N_Q), fs=16, bold=True))
        box.add_widget(self.button(self.bt('start', 16, 100), self.tv_start))
        box.add_widget(self.button(self.bt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def tv_start(self):
        self.tv_qs = random.sample(range(len(bd.TRIVIA)), N_Q)
        self.tv_i = 0
        self.tv_score = 0
        self.tv_new_best = False
        self.tv_next_question()
        self.go('tv_q')

    def tv_next_question(self):
        q = bd.TRIVIA[self.tv_qs[self.tv_i]]
        order = list(range(len(q[2])))
        random.shuffle(order)
        self.tv_opts = order          # ترتيب الخيارات المعروض
        self.tv_pick = None

    def show_tv_q(self, box):
        app = App.get_running_app()
        q = bd.TRIVIA[self.tv_qs[self.tv_i]]
        box.add_widget(self.label(self.bt('progress', 13, 60, i=self.tv_i + 1, n=N_Q), fs=13,
                                  color=app.muted_color))
        box.add_widget(self.label(self.pair(q[0], q[1], 20, 50), fs=20, bold=True))
        for oi in self.tv_opts:
            o = q[2][oi]
            box.add_widget(self.button(self.pair(o[0], o[1], 16, 110),
                                       lambda oi=oi: self.tv_answer(oi)))
        box.add_widget(self.button(self.bt('menu', 15, 100), lambda: self.go('tv_home'), gray=True))

    def tv_answer(self, oi):
        q = bd.TRIVIA[self.tv_qs[self.tv_i]]
        self.tv_pick = oi
        if oi == q[3]:
            self.tv_score += 1
        self.go('tv_fb')

    def show_tv_fb(self, box):
        q = bd.TRIVIA[self.tv_qs[self.tv_i]]
        ok = self.tv_pick == q[3]
        box.add_widget(self.label(self.pair(q[0], q[1], 17, 60), fs=17, bold=True))
        box.add_widget(self.label(self.bt('right' if ok else 'wrong', 24), fs=24, bold=True,
                                  color=GREEN if ok else RED))
        if not ok:
            o = q[2][q[3]]
            box.add_widget(self.label(self.bt('ans', 18, 60, a=self.raw2(o[0], o[1])), fs=18))
        last = self.tv_i + 1 >= N_Q
        box.add_widget(self.button(self.bt('finish' if last else 'next', 16, 100), self.tv_next))

    def tv_next(self):
        self.tv_i += 1
        if self.tv_i >= N_Q:
            best = self.tv_best()
            if self.tv_score > best:
                self.tv_new_best = True
                try:
                    core._write(BEST_FILE, {'best': self.tv_score})
                except Exception as e:
                    core.log(f"trivia best: {e}")
            self.go('tv_end')
        else:
            self.tv_next_question()
            self.go('tv_q')

    def show_tv_end(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.bt('score_head', 16), fs=16, color=app.muted_color))
        box.add_widget(self.label(f"{self.tv_score} / {N_Q}", fs=44, bold=True,
                                  color=app.primary_color))
        if self.tv_new_best:
            box.add_widget(self.label(self.bt('new_best', 18), fs=18, bold=True, color=GREEN))
        else:
            box.add_widget(self.label(self.bt('best', 15, 60, n=self.tv_best(), t=N_Q), fs=15,
                                      color=app.muted_color))
        box.add_widget(self.button(self.bt('again', 16, 100), self.tv_start))
        box.add_widget(self.button(self.bt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    # ---------- ألغاز ----------
    def show_rd_home(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.bt('rd_head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.bt('rd_desc', 15), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.bt('start', 16, 100), self.rd_start))
        box.add_widget(self.button(self.bt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def rd_draw(self):
        if not self.rd_deck:
            self.rd_deck = list(range(len(bd.RIDDLES)))
            random.shuffle(self.rd_deck)
        self.rd_cur = bd.RIDDLES[self.rd_deck.pop()]
        self.rd_hint = False
        self.rd_ans = False

    def rd_start(self):
        self.rd_draw()
        self.go('rd_card')

    def show_rd_card(self, box):
        app = App.get_running_app()
        r = self.rd_cur
        card = Factory.GiftCard()
        card.add_widget(self.label(self.pair(r[0], r[1], 20, 90), fs=20, bold=True))
        box.add_widget(card)
        if self.rd_hint:
            box.add_widget(self.label(self.pair(r[2], r[3], 15, 60), fs=15, color=app.muted_color))
        if self.rd_ans:
            box.add_widget(self.label(self.pair(r[4], r[5], 22, 60), fs=22, bold=True,
                                      color=app.primary_color))
        if not self.rd_hint and not self.rd_ans:
            box.add_widget(self.button(self.bt('hint', 15, 100), self.rd_show_hint, gray=True))
        if not self.rd_ans:
            box.add_widget(self.button(self.bt('answer', 16, 100), self.rd_show_ans))
        box.add_widget(self.button(self.bt('next_r', 16, 100), self.rd_next))
        box.add_widget(self.button(self.bt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def rd_show_hint(self):
        self.rd_hint = True
        self.render()

    def rd_show_ans(self):
        self.rd_ans = True
        self.render()

    def rd_next(self):
        self.rd_draw()
        self.render()
