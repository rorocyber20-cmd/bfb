"""لعبة "من يعرفني أكثر": بنك الأسئلة + ترميز الإجابات في كود قصير.
لا يعتمد على Kivy، فيمكن تجربته وحده.

مهم جدًا: بنك الأسئلة POOL يُضاف إليه فقط من النهاية. لا تحذف سؤالًا ولا تغيّر ترتيبه
ولا ترتيب خياراته، وإلا لن تُفهم الأكواد القديمة التي أرسلها الأصدقاء.
"""
import base64
import os
import random
import re

VERSION = 1
QUESTIONS_PER_QUIZ = 10
MAX_NAME_BYTES = 20

# كل سؤال: (إنجليزي، عربي، [(إنجليزي، عربي), ...]) وبحد أقصى 8 خيارات و32 سؤالًا
POOL = [
    ('Which hand is used for writing?', 'اليد المستعملة في الكتابة؟',
     [('Right', 'اليمنى'), ('Left', 'اليسرى'), ('Both', 'كلتاهما')]),
    ('Favorite food', 'الأكلة المفضلة',
     [('Couscous', 'الكسكسي'), ('Pizza', 'البيتزا'), ('Burger', 'البرغر'),
      ('Tacos', 'التاكوس'), ('Shawarma', 'الشاورما'), ('Pasta', 'المعكرونة')]),
    ('Favorite drink', 'المشروب المفضل',
     [('Coffee', 'القهوة'), ('Tea', 'الشاي'), ('Juice', 'العصير'),
      ('Soda', 'المشروبات الغازية'), ('Water', 'الماء'), ('Milkshake', 'الميلك شيك')]),
    ('Morning person or night owl?', 'صباحي أم سهران؟',
     [('Morning person', 'صباحي'), ('Night owl', 'سهران'), ('Depends on the day', 'حسب اليوم')]),
    ('Favorite season', 'الفصل المفضل',
     [('Spring', 'الربيع'), ('Summer', 'الصيف'), ('Autumn', 'الخريف'), ('Winter', 'الشتاء')]),
    ('Favorite place to relax', 'المكان المفضل للاستجمام',
     [('The sea', 'البحر'), ('The mountains', 'الجبل'), ('The desert', 'الصحراء'),
      ('The city', 'المدينة'), ('At home', 'البيت')]),
    ('Favorite color', 'اللون المفضل',
     [('Blue', 'الأزرق'), ('Red', 'الأحمر'), ('Green', 'الأخضر'),
      ('Black', 'الأسود'), ('Purple', 'البنفسجي'), ('Yellow', 'الأصفر')]),
    ('Favorite pet', 'الحيوان الأليف المفضل',
     [('Cat', 'القط'), ('Dog', 'الكلب'), ('Bird', 'الطائر'), ('No pets', 'لا أحب الحيوانات الأليفة')]),
    ('Favorite movie genre', 'نوع الأفلام المفضل',
     [('Comedy', 'كوميديا'), ('Action', 'أكشن'), ('Horror', 'رعب'),
      ('Romance', 'رومانسي'), ('Anime', 'أنمي'), ('Documentary', 'وثائقي')]),
    ('Preferred way to reach people', 'الطريقة المفضلة للتواصل',
     [('Text messages', 'الرسائل النصية'), ('Voice notes', 'الرسائل الصوتية'), ('Phone calls', 'المكالمات')]),
    ('Favorite sport or activity', 'الرياضة أو النشاط المفضل',
     [('Football', 'كرة القدم'), ('Basketball', 'كرة السلة'), ('Swimming', 'السباحة'),
      ('Gym', 'قاعة الرياضة'), ('Gaming', 'الألعاب الإلكترونية'), ('None', 'لا شيء')]),
    ('Favorite way to spend free time', 'أفضل طريقة لقضاء وقت الفراغ',
     [('Sleeping', 'النوم'), ('Gaming', 'اللعب'), ('Watching series', 'مشاهدة المسلسلات'),
      ('Going out', 'الخروج'), ('Reading', 'القراءة'), ('Social media', 'مواقع التواصل')]),
    ('Favorite sweet', 'الحلوى المفضلة',
     [('Chocolate', 'الشوكولاتة'), ('Ice cream', 'المثلجات'), ('Cake', 'الكيك'),
      ('Baklava', 'البقلاوة'), ('Dates', 'التمر')]),
    ('Phone brand', 'ماركة الهاتف',
     [('Samsung', 'سامسونغ'), ('iPhone', 'آيفون'), ('Xiaomi', 'شاومي'),
      ('Huawei', 'هواوي'), ('Other', 'أخرى')]),
    ('Sweet or salty?', 'حلو أم مالح؟',
     [('Sweet', 'حلو'), ('Salty', 'مالح'), ('Both', 'الاثنان')]),
    ('Ideal birthday celebration', 'الاحتفال المثالي بعيد الميلاد',
     [('A big party', 'حفلة كبيرة'), ('Family dinner', 'عشاء عائلي'),
      ('Outing with friends', 'خروج مع الأصدقاء'), ('Just another day', 'يوم عادي')]),
    ('Biggest fear', 'أكبر خوف',
     [('Heights', 'المرتفعات'), ('Insects', 'الحشرات'), ('Darkness', 'الظلام'),
      ('Deep water', 'المياه العميقة'), ('Public speaking', 'الحديث أمام الناس'), ('Failure', 'الفشل')]),
    ('Superpower to choose', 'القوة الخارقة المختارة',
     [('Flying', 'الطيران'), ('Invisibility', 'الاختفاء'), ('Reading minds', 'قراءة الأفكار'),
      ('Time travel', 'السفر عبر الزمن'), ('Super strength', 'القوة الخارقة'), ('Teleporting', 'الانتقال الفوري')]),
    ('Favorite social app', 'تطبيق التواصل المفضل',
     [('Instagram', 'إنستغرام'), ('TikTok', 'تيك توك'), ('WhatsApp', 'واتساب'),
      ('Snapchat', 'سناب شات'), ('YouTube', 'يوتيوب'), ('Facebook', 'فيسبوك')]),
    ('Early or late?', 'مواعيده عادةً',
     [('Always early', 'دائمًا مبكر'), ('On time', 'في الوقت'), ('Usually late', 'غالبًا متأخر')]),
    ('Dream travel destination', 'وجهة السفر المفضلة',
     [('Turkey', 'تركيا'), ('Europe', 'أوروبا'), ('Dubai', 'دبي'),
      ('Japan or Korea', 'اليابان أو كوريا'), ('USA', 'أمريكا'), ('Holy lands', 'الأراضي المقدسة')]),
    ('Cook or order?', 'الطبخ أم الطلب الجاهز؟',
     [('Cook at home', 'الطبخ في البيت'), ('Order food', 'طلب الأكل'), ('Eat what is ready', 'أكل ما هو جاهز')]),
    ('Favorite music', 'الموسيقى المفضلة',
     [('Rai', 'الراي'), ('Rap', 'الراب'), ('Pop', 'البوب'),
      ('Chaabi', 'الشعبي'), ('Nasheeds', 'الأناشيد'), ('Not into music', 'لا يستمع كثيرًا')]),
    ('First thing after waking up', 'أول شيء بعد الاستيقاظ',
     [('Check the phone', 'تفقد الهاتف'), ('Coffee or tea', 'القهوة أو الشاي'),
      ('Go back to sleep', 'العودة إلى النوم'), ('Take a shower', 'الاستحمام')]),
    ('Language used in chats', 'لغة المحادثات',
     [('Arabic', 'العربية'), ('French', 'الفرنسية'), ('English', 'الإنجليزية'), ('A mix of all', 'خليط من الكل')]),
    ('Most valued trait in a friend', 'أهم صفة في الصديق',
     [('Loyalty', 'الوفاء'), ('Humor', 'روح الدعابة'), ('Honesty', 'الصدق'),
      ('Generosity', 'الكرم'), ('Intelligence', 'الذكاء')]),
    ('How to handle stress', 'طريقة التعامل مع التوتر',
     [('Sleep', 'النوم'), ('Eat', 'الأكل'), ('Exercise', 'الرياضة'),
      ('Talk to someone', 'التحدث مع شخص'), ('Stay alone', 'البقاء وحيدًا')]),
    ('Favorite day of the week', 'اليوم المفضل في الأسبوع',
     [('Thursday', 'الخميس'), ('Friday', 'الجمعة'), ('Saturday', 'السبت'), ('Any weekday', 'أي يوم عادي')]),
    ('Introvert or extrovert?', 'انطوائي أم اجتماعي؟',
     [('Introvert', 'انطوائي'), ('Extrovert', 'اجتماعي'), ('A bit of both', 'مزيج من الاثنين')]),
    ('Favorite school subject', 'المادة المفضلة في المدرسة',
     [('Math', 'الرياضيات'), ('Science', 'العلوم'), ('Languages', 'اللغات'),
      ('History', 'التاريخ'), ('Art', 'الفنون'), ('Sports', 'الرياضة البدنية')]),
]

assert len(POOL) <= 32
assert all(2 <= len(q[2]) <= 8 for q in POOL)


# ---------------------------------------------------------------
# اختيار الأسئلة
# ---------------------------------------------------------------
def pick_question_ids(n=QUESTIONS_PER_QUIZ, rng=None):
    rng = rng or random
    return rng.sample(range(len(POOL)), n)


# ---------------------------------------------------------------
# الترميز: [الإصدار][nonce][طول الاسم] + 10 بايتات (سؤال<<3 | إجابة) + الاسم + المجموع الاختباري
# ما بعد الرأس يُخلَط بمفتاح من nonce كي لا تُقرأ الإجابات بالعين المجرّدة (حماية خفيفة بين الأصدقاء).
# ---------------------------------------------------------------
def _stream(nonce, n):
    x = (nonce * 167 + 13) & 0xFF
    out = []
    for _ in range(n):
        x = (x * 73 + 41) & 0xFF
        out.append(x)
    return out


def _checksum(data):
    return (sum(data) * 31 + 7) & 0xFF


def _trim_name(name):
    name = (name or '').strip()
    while len(name.encode('utf-8')) > MAX_NAME_BYTES:
        name = name[:-1]
    return name


def encode(name, qa, nonce=None):
    """qa: قائمة (رقم السؤال، رقم الإجابة). يرجع كودًا مثل BFB-ABCDE-FGHIJ-..."""
    if len(qa) != QUESTIONS_PER_QUIZ:
        raise ValueError('wrong number of answers')
    name_b = _trim_name(name).encode('utf-8')
    body = []
    for qid, ans in qa:
        if not (0 <= qid < len(POOL)) or not (0 <= ans < len(POOL[qid][2])):
            raise ValueError('bad answer')
        body.append((qid << 3) | ans)
    body += list(name_b)
    nonce = random.randrange(256) if nonce is None else nonce
    mixed = [b ^ k for b, k in zip(body, _stream(nonce, len(body)))]
    head = [VERSION, nonce, len(name_b)]
    raw = head + mixed
    raw.append(_checksum(raw))
    text = base64.b32encode(bytes(raw)).decode('ascii').rstrip('=')
    return 'BFB-' + '-'.join(text[i:i + 5] for i in range(0, len(text), 5))


_CODE_RE = re.compile(r'BFB-([A-Z2-7]{1,5}(?:-[A-Z2-7]{1,5})*)', re.IGNORECASE)


def extract_code(text):
    """يستخرج الكود من نص لصقه المستخدم (حتى لو لصق رسالة كاملة)."""
    if not text:
        return None
    m = _CODE_RE.search(text)
    return m.group(1).upper().replace('-', '') if m else None


def decode(text):
    """يرجع {'name': ..., 'qa': [(qid, ans), ...]} أو يرفع ValueError."""
    payload = extract_code(text)
    if not payload:
        raise ValueError('no code')
    try:
        raw = base64.b32decode(payload + '=' * (-len(payload) % 8))
    except Exception:
        raise ValueError('bad base32')
    if len(raw) < 3 + QUESTIONS_PER_QUIZ + 1:
        raise ValueError('too short')
    if _checksum(list(raw[:-1])) != raw[-1]:
        raise ValueError('checksum')
    version, nonce, name_len = raw[0], raw[1], raw[2]
    if version != VERSION:
        raise ValueError('version')
    mixed = list(raw[3:-1])
    if len(mixed) != QUESTIONS_PER_QUIZ + name_len:
        raise ValueError('length')
    body = [b ^ k for b, k in zip(mixed, _stream(nonce, len(mixed)))]
    qa = []
    seen = set()
    for b in body[:QUESTIONS_PER_QUIZ]:
        qid, ans = b >> 3, b & 7
        if qid >= len(POOL) or ans >= len(POOL[qid][2]) or qid in seen:
            raise ValueError('bad question')
        seen.add(qid)
        qa.append((qid, ans))
    try:
        name = bytes(body[QUESTIONS_PER_QUIZ:]).decode('utf-8')
    except Exception:
        raise ValueError('bad name')
    return {'name': name, 'qa': qa}


def score(correct_qa, guesses):
    """عدد الإجابات الصحيحة. كلاهما قائمة إجابات بنفس ترتيب الأسئلة."""
    return sum(1 for (qid, ans), g in zip(correct_qa, guesses) if ans == g)
