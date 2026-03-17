"""
Google Gemini API — анализ брифа и генерация мудборда
Бесплатный тариф: 60 запросов/мин, 1500 запросов/день
Получить ключ: https://aistudio.google.com/app/apikey
"""

import google.generativeai as genai
import config

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def format_brief_for_prompt(data: dict) -> str:
    return f"""
БРЕНД:
- Название: {data.get('brand_name', '—')}
- Сфера: {data.get('brand_sphere', '—')}
- Продукт/услуга: {data.get('brand_product', '—')}
- Миссия: {data.get('brand_mission', '—')}
- Ценности: {data.get('brand_values', '—')}
- История бренда: {data.get('brand_story', '—')}

ЦЕЛЕВАЯ АУДИТОРИЯ:
- Портрет покупателя: {data.get('audience_who', '—')}
- Боль/проблема: {data.get('audience_pain', '—')}
- Желание/мечта: {data.get('audience_desire', '—')}

КОНКУРЕНТЫ:
- Конкуренты: {data.get('competitors_who', '—')}
- Отличие от конкурентов: {data.get('competitors_diff', '—')}

ВИЗУАЛЬНЫЕ ПРЕДПОЧТЕНИЯ:
- Нравится (примеры): {data.get('visual_like', '—')}
- Не нравится: {data.get('visual_dislike', '—')}
- Желаемое настроение: {data.get('visual_mood', '—')}
- Предпочтения по стилю: {data.get('visual_style', '—')}

АССОЦИАЦИИ И ХАРАКТЕР:
- 5 ключевых слов: {data.get('assoc_words', '—')}
- Бренд как человек: {data.get('assoc_person', '—')}
- Бренд как место: {data.get('assoc_place', '—')}
- Желаемое чувство: {data.get('assoc_feeling', '—')}

ДОПОЛНИТЕЛЬНО:
- Прочие пожелания: {data.get('extra_notes', '—')}
"""


async def analyze_brief(data: dict) -> dict:
    brief_text = format_brief_for_prompt(data)

    # Шаг 1: глубокий анализ бренда
    analysis_prompt = f"""Ты — опытный бренд-стратег и арт-директор с 15-летним опытом.
Тебе предоставлен бриф от заказчика. Проведи глубокий анализ.

=== БРИФ ===
{brief_text}
============

Проведи анализ по этим блокам:

1. СУТЬ БРЕНДА
- Архетип бренда (Герой, Любовник, Мудрец, Маг, Бунтарь, Правитель и т.д.)
- Позиционирование в 1–2 предложениях
- Главный insight — что-то неочевидное, но важное

2. АНАЛИЗ ЦА
- Психографика: ценности, образ жизни, поведение
- Эмоциональные триггеры
- Момент контакта с брендом

3. КОНКУРЕНТНОЕ ПОЛЕ
- Визуальные клише в нише
- Пробел — что визуально не занято конкурентами
- Как выделиться

4. ВИЗУАЛЬНАЯ КОНЦЕПЦИЯ
- 2 концептуальных направления с названием и сутью
- Для каждого: образный ряд, настроение

5. ЭМОЦИОНАЛЬНАЯ КАРТА
- Что бренд говорит (рационально)
- Что бренд ощущается (эмоционально)

Пиши развёрнуто и профессионально."""

    analysis_response = model.generate_content(analysis_prompt)
    analysis_text = analysis_response.text

    # Шаг 2: извлечь конкретные параметры для мудборда
    extract_prompt = f"""На основе анализа бренда извлеки конкретные параметры.

АНАЛИЗ:
{analysis_text}

Верни ТОЛЬКО в таком формате, без лишних слов, каждый параметр с новой строки:

ARCHETYPE: [архетип]
POSITIONING: [позиционирование в 1 предложении]
INSIGHT: [главный инсайт]
CONCEPT_NAME: [название главной концепции]
CONCEPT_ESSENCE: [суть концепции 2–3 предложения]
COLORS_PRIMARY: [3 цвета: название — #hex, через запятую]
COLORS_ACCENT: [1–2 акцентных цвета: название — #hex]
COLORS_MOOD: [описание цветового настроения]
TYPOGRAPHY_DISPLAY: [шрифт для заголовков с обоснованием]
TYPOGRAPHY_BODY: [шрифт для текста]
TYPOGRAPHY_STYLE: [описание типографического стиля]
IMAGERY_STYLE: [стиль изображений]
IMAGERY_SCENES: [3–5 сцен через запятую]
IMAGERY_AVOID: [что избегать]
TEXTURE_MATERIAL: [фактуры и материалы]
COMPOSITION: [принцип композиции]
REFERENCES: [5–7 референсов: бренды/художники через запятую]
EMOTION_TRIGGER: [ключевое эмоциональное послание]
TAGLINE_IDEAS: [2–3 идеи слогана через | ]"""

    extract_response = model.generate_content(extract_prompt)
    params_text = extract_response.text

    # Парсим параметры
    params = {}
    for line in params_text.strip().split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if key and value:
                params[key] = value

    return {
        "full_analysis": analysis_text,
        "params": params
    }


async def generate_moodboard_text(data: dict, analysis: dict) -> str:
    params = analysis.get("params", {})
    brief_text = format_brief_for_prompt(data)

    moodboard_prompt = f"""Ты — арт-директор, создаёшь текстовый мудборд для бренда.
Пиши вдохновляюще, образно, профессионально.

БРИФ:
{brief_text}

ПАРАМЕТРЫ КОНЦЕПЦИИ:
Архетип: {params.get('ARCHETYPE', '—')}
Концепция: {params.get('CONCEPT_NAME', '—')} — {params.get('CONCEPT_ESSENCE', '—')}
Цвета: {params.get('COLORS_PRIMARY', '—')} | Акцент: {params.get('COLORS_ACCENT', '—')}
Настроение: {params.get('COLORS_MOOD', '—')}
Типографика: {params.get('TYPOGRAPHY_DISPLAY', '—')}
Образный ряд: {params.get('IMAGERY_SCENES', '—')}
Ключевая эмоция: {params.get('EMOTION_TRIGGER', '—')}

Создай красивый мудборд для Telegram с Markdown (*жирный*, _курсив_).
Структура:

✦ НАЗВАНИЕ БРЕНДА · АРХЕТИП

*КОНЦЕПЦИЯ*
[поэтичное описание идеи]

*🎨 ЦВЕТОВАЯ ПАЛИТРА*
[цвета с hex-кодами и описанием настроения]

*✍️ ТИПОГРАФИКА*
[шрифты и стиль]

*📸 ОБРАЗНЫЙ РЯД*
[что снимать, какие сцены и образы]

*🧱 ФАКТУРЫ И МАТЕРИАЛЫ*
[текстуры, материалы]

*📐 КОМПОЗИЦИЯ*
[принцип построения кадра и макета]

*🔖 РЕФЕРЕНСЫ*
[бренды и художники]

*💬 ИДЕИ СЛОГАНОВ*
[2–3 варианта]

*✉️ ПОСЛАНИЕ ДИЗАЙНЕРУ*
[финальная мысль — что самое важное донести визуалом]"""

    response = model.generate_content(moodboard_prompt)
    return response.text
