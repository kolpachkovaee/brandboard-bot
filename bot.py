"""
Design Brief Bot — Telegram бот-помощник дизайнера
Собирает бриф, анализирует, генерирует мудборд
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import config
from gemini_analyzer import analyze_brief, generate_moodboard_text
from pdf_generator import generate_brief_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ─── FSM States ───────────────────────────────────────────────────────────────

class Brief(StatesGroup):
    # Блок 1: О бренде
    brand_name        = State()
    brand_sphere      = State()
    brand_product     = State()
    brand_mission     = State()
    brand_values      = State()
    brand_story       = State()

    # Блок 2: Целевая аудитория
    audience_who      = State()
    audience_pain     = State()
    audience_desire   = State()

    # Блок 3: Конкуренты
    competitors_who   = State()
    competitors_diff  = State()

    # Блок 4: Визуальные предпочтения
    visual_like       = State()
    visual_dislike    = State()
    visual_mood       = State()
    visual_style      = State()

    # Блок 5: Ассоциации и характер
    assoc_words       = State()
    assoc_person      = State()
    assoc_place       = State()
    assoc_feeling     = State()

    # Финал
    extra_notes       = State()
    processing        = State()


# ─── Вопросы брифа ────────────────────────────────────────────────────────────

QUESTIONS = {
    Brief.brand_name:      "1/20 ✦ Как называется бренд или проект?",
    Brief.brand_sphere:    "2/20 ✦ В какой сфере работает бренд? (мода, еда, tech, beauty, услуги...)",
    Brief.brand_product:   "3/20 ✦ Что именно продаёте или предлагаете? Опишите продукт/услугу.",
    Brief.brand_mission:   "4/20 ✦ В чём миссия бренда? Ради чего он существует?",
    Brief.brand_values:    "5/20 ✦ Назовите 3–5 ключевых ценностей бренда.",
    Brief.brand_story:     "6/20 ✦ Расскажите историю или легенду бренда. Как и почему он появился?",

    Brief.audience_who:    "7/20 ✦ Опишите вашего идеального покупателя. Возраст, образ жизни, интересы.",
    Brief.audience_pain:   "8/20 ✦ Какую боль или проблему решает ваш продукт для этого человека?",
    Brief.audience_desire: "9/20 ✦ О чём мечтает ваш покупатель? Чего он хочет достичь?",

    Brief.competitors_who:  "10/20 ✦ Назовите 2–3 главных конкурента (бренды, ссылки или описания).",
    Brief.competitors_diff: "11/20 ✦ Чем вы принципиально отличаетесь от конкурентов?",

    Brief.visual_like:     "12/20 ✦ Назовите 2–3 бренда, чей визуал вам нравится (и почему).",
    Brief.visual_dislike:  "13/20 ✦ Есть ли визуальные стили, которые вам точно НЕ нравятся?",
    Brief.visual_mood:     "14/20 ✦ Выберите настроение визуала:\nСтрого / Игриво\nМинимализм / Насыщенность\nТепло / Холодно\nЛаконично / Детально\n\nОпишите желаемое настроение своими словами.",
    Brief.visual_style:    "15/20 ✦ Есть ли предпочтения по стилю?\n(Например: минимализм, ретро, граффити, люкс, эко, tech, арт...)",

    Brief.assoc_words:     "16/20 ✦ Напишите 5 слов, которые должны ассоциироваться с брендом.",
    Brief.assoc_person:    "17/20 ✦ Если бы бренд был человеком — кто это? (Опишите характер, профессию, образ жизни)",
    Brief.assoc_place:     "18/20 ✦ Если бы бренд был местом — каким? (кафе в Токио, лес на рассвете, студия в Нью-Йорке...)",
    Brief.assoc_feeling:   "19/20 ✦ Какое чувство должен испытывать человек, увидев визуал бренда?",

    Brief.extra_notes:     "20/20 ✦ Есть ли что-то важное, что не вошло в вопросы? Любые пожелания, ограничения, вдохновение.",
}

FIELD_NAMES = {
    Brief.brand_name:       "brand_name",
    Brief.brand_sphere:     "brand_sphere",
    Brief.brand_product:    "brand_product",
    Brief.brand_mission:    "brand_mission",
    Brief.brand_values:     "brand_values",
    Brief.brand_story:      "brand_story",
    Brief.audience_who:     "audience_who",
    Brief.audience_pain:    "audience_pain",
    Brief.audience_desire:  "audience_desire",
    Brief.competitors_who:  "competitors_who",
    Brief.competitors_diff: "competitors_diff",
    Brief.visual_like:      "visual_like",
    Brief.visual_dislike:   "visual_dislike",
    Brief.visual_mood:      "visual_mood",
    Brief.visual_style:     "visual_style",
    Brief.assoc_words:      "assoc_words",
    Brief.assoc_person:     "assoc_person",
    Brief.assoc_place:      "assoc_place",
    Brief.assoc_feeling:    "assoc_feeling",
    Brief.extra_notes:      "extra_notes",
}

STATE_ORDER = list(QUESTIONS.keys())


# ─── Handlers ─────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я *Design Brief Bot* — помогу тебе и дизайнеру создать сильный визуальный стиль.\n\n"
        "Я задам 20 вопросов о твоём бренде, а потом:\n"
        "• Проанализирую бренд, ЦА и конкурентов\n"
        "• Составлю текстовый мудборд с концепцией\n"
        "• Дам направление по цветам, типографике и образам\n"
        "• Создам PDF-бриф для дизайнера\n\n"
        "Это займёт около 10 минут. Начнём?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Начать бриф ✦")]],
            resize_keyboard=True
        )
    )


@dp.message(F.text == "Начать бриф ✦")
async def start_brief(message: types.Message, state: FSMContext):
    await state.set_state(Brief.brand_name)
    await message.answer(
        QUESTIONS[Brief.brand_name],
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Command("restart"))
async def cmd_restart(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)


async def handle_answer(message: types.Message, state: FSMContext, current_state):
    """Универсальный обработчик для всех вопросов брифа"""
    field = FIELD_NAMES[current_state]
    await state.update_data(**{field: message.text})

    current_index = STATE_ORDER.index(current_state)

    # Показываем блочные разделители
    block_intros = {
        2: "*Блок 2: Целевая аудитория*\n",
        4: "*Блок 3: Конкуренты*\n",
        5: "*Блок 4: Визуальные предпочтения*\n",
        7: "*Блок 5: Ассоциации и характер бренда*\n",
    }

    if current_index + 1 < len(STATE_ORDER):
        next_state = STATE_ORDER[current_index + 1]
        intro = block_intros.get(current_index + 1, "")

        await state.set_state(next_state)
        await message.answer(
            intro + QUESTIONS[next_state],
            parse_mode="Markdown"
        )
    else:
        # Все вопросы заданы — запускаем анализ
        await state.set_state(Brief.processing)
        processing_msg = await message.answer(
            "Отлично! Собрал все ответы.\n\n"
            "Анализирую бренд, ЦА и конкурентов...\n"
            "Составляю концепцию мудборда...\n\n"
            "_Это займёт 30–60 секунд_",
            parse_mode="Markdown"
        )

        data = await state.get_data()

        try:
            # Анализ через Claude
            analysis = await analyze_brief(data)
            moodboard = await generate_moodboard_text(data, analysis)

            # Генерация PDF
            pdf_path = await generate_brief_pdf(data, analysis, moodboard, message.from_user.id)

            # Отправляем мудборд текстом
            await message.answer(moodboard, parse_mode="Markdown")

            # Отправляем PDF
            with open(pdf_path, "rb") as pdf_file:
                await message.answer_document(
                    types.BufferedInputFile(pdf_file.read(), filename="brand_brief.pdf"),
                    caption="📄 Полный бриф для дизайнера"
                )

            await message.answer(
                "Готово! Мудборд и бриф составлены.\n\n"
                "Поделитесь этим PDF с дизайнером — у него будет полная картина.\n\n"
                "Хотите начать заново? /restart",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="Начать новый бриф")]],
                    resize_keyboard=True
                )
            )

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            await message.answer(
                "Произошла ошибка при анализе. Попробуйте /restart\n\n"
                f"Детали: {str(e)[:200]}"
            )

        await state.clear()


# Регистрируем обработчики для каждого состояния
for _state in STATE_ORDER:
    dp.message.register(
        lambda msg, st, s=_state: handle_answer(msg, st, s),
        StateFilter(_state)
    )


@dp.message(F.text == "Начать новый бриф")
async def new_brief(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main():
    import os
    from aiohttp import web

    async def health(request):
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info("Starting Design Brief Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
