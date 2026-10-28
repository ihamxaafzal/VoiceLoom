"""Kokoro local voices and a verified snapshot of Edge English voices."""
import json
import re
from pathlib import Path
LANGUAGES = {'a': 'American English', 'b': 'British English', 'e': 'Spanish',
             'f': 'French', 'h': 'Hindi', 'i': 'Italian', 'j': 'Japanese',
             'p': 'Portuguese (Brazil)', 'z': 'Mandarin Chinese'}
GROUPS = {
    'af': 'heart alloy aoede bella jessica kore nicole nova river sarah sky',
    'am': 'adam echo eric fenrir liam michael onyx puck santa',
    'bf': 'alice emma isabella lily', 'bm': 'daniel fable george lewis',
    'ef': 'dora', 'em': 'alex santa', 'ff': 'siwis',
    'hf': 'alpha beta', 'hm': 'omega psi', 'if': 'sara', 'im': 'nicola',
    'jf': 'alpha gongitsune nezumi tebukuro', 'jm': 'kumo',
    'pf': 'dora', 'pm': 'alex santa',
    'zf': 'xiaobei xiaoni xiaoxiao xiaoyi', 'zm': 'yunjian yunxi yunxia yunyang',
}
VOICES = [dict(id=f'{prefix}_{name}', name=name.title(), language=LANGUAGES[prefix[0]],
               code=prefix[0], gender='Female' if prefix[1] == 'f' else 'Male', engine='kokoro')
          for prefix, names in GROUPS.items() for name in names.split()]
REGIONS = {'AU': 'Australian English', 'CA': 'Canadian English', 'HK': 'Hong Kong English',
           'IN': 'Indian English', 'IE': 'Irish English', 'KE': 'Kenyan English',
           'NZ': 'New Zealand English', 'NG': 'Nigerian English', 'PH': 'Philippine English',
           'SG': 'Singapore English', 'ZA': 'South African English', 'TZ': 'Tanzanian English'}
ENGLISH_CODES = {'a', 'b'}
for record in json.loads(Path(__file__).with_name('english_voices.json').read_text(encoding='utf-8')):
    locale = record['Locale']
    code = {'en-US': 'a', 'en-GB': 'b'}.get(locale, locale)
    if code not in LANGUAGES:
        LANGUAGES[code] = REGIONS[locale.split('-')[1]]
    ENGLISH_CODES.add(code)
    name = record['ShortName'].split('-', 2)[2].removesuffix('Neural')
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    VOICES.append(dict(id=record['ShortName'], name=name, language=LANGUAGES[code],
                       code=code, gender=record['Gender'], engine='edge'))
BY_ID = {v['id']: v for v in VOICES}
SAMPLES = {
 'a': 'Every great story begins with a single word. Bring your ideas to life with a voice that feels natural.',
 'b': 'Every great story begins with a single word. Let us discover something extraordinary together.',
 'e': 'Cada gran historia comienza con una palabra. Descubramos juntos un mundo de nuevas ideas.',
 'f': 'Chaque grande histoire commence par un mot. Découvrons ensemble un monde de nouvelles idées.',
 'h': 'हर बड़ी कहानी एक शब्द से शुरू होती है। आइए मिलकर नए विचारों की दुनिया खोजें।',
 'i': 'Ogni grande storia inizia con una parola. Scopriamo insieme un mondo di nuove idee.',
 'j': 'すべての素晴らしい物語は、一つの言葉から始まります。一緒に新しい世界を見つけましょう。',
 'p': 'Toda grande história começa com uma palavra. Vamos descobrir juntos um mundo de novas ideias.',
 'z': '每一个精彩的故事都从一个词开始。让我们一起探索充满新想法的世界。',
}
for code in ENGLISH_CODES:
    SAMPLES.setdefault(code, SAMPLES['a'])


def can_blend(first, second):
    return (first.get('engine', 'kokoro') == second.get('engine', 'kokoro') == 'kokoro'
            and first['code'] == second['code'] and first['id'] != second['id'])
