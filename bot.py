import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import config
from gemini_analyzer import analyze_brief

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Brief(StatesGroup):
    q1  = State()
    q2  = State()
    q3  = State()
    q4  = State()
    q5  = State()
    q6  = State()
    q7  = State()
    q8  = State()
    q9  = State()
    q10 = State()


QUESTIONS = [
    "1/10 ✦ Как называется бренд и чем он занимается?",
    "2/10 ✦ Какой главный продукт или услуга? Опишите в 2–3 предложениях.",
    "3/10 ✦ В чём миссия бренда и его ключевые ценности?",
    "4/10 ✦ Опишите идеального покупателя — возраст, образ жизни, интересы.",
    "5/10 ✦ Какую боль или проблему решает ваш продукт?",
    "6/10 ✦ Назовите 2–3 конкурента. Чем вы от них отличаетесь?",
    "7/10 ✦ Назовите 2–3 бренда, чей визуал вам нравится — и почему.",
    "8/10 ✦ Опишите желаемое настроение визуала.\nНапример: строго/игриво, минимализм/яркость, тепло/холодно.",
    "9/10 ✦ Напишите 5 слов, которые должны ассоциироваться с брендом.",
    "10/10 ✦ Если бы бренд был человеком — кто это? Характер, стиль, профессия.",
]

FIELDS = ["brand", "product", "mission", "audience", "pain", "competitors", "visual_like", "mood", "words", "person"]
STATES = [Brief.q1, Brief.q2, Brief.q3, Brief.q4, Brief.q5, Brief.q6, Brief.q7, Brief.q8, Brief.q9, Brief.q10]


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✦ *Brandboard*\n\n"
        "Помогу превратить идею бренда в чёткую визуальную концепцию.\n\n"
        "Отвечу на 10 вопросов — и получишь готовый мудборд с палитрой, типографикой и образами.\n\n"
        "Поехали?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Начать ✦")]],
            resize_keyboard=True
        )
    )


@dp.message(F.text == "Начать ✦")
@dp.message(F.text == "Начать заново ✦")
async def start_brief(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Brief.q1)
    await message.answer(QUESTIONS[0], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")


@dp.message(Command("restart"))
async def cmd_restart(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)


async def next_question(message: types.Message, state: FSMContext, current_index: int, answer: str):
    field = FIELDS[current_index]
    await state.update_data(**{field: answer})

    next_index = current_index + 1

    if next_index < len(QUESTIONS):
        next_state = STATES[next_index]
        await state.set_state(next_state)
        await message.answer(QUESTIONS[next_index], parse_mode="Markdown")
    else:
        await state.set_state(None)
        await message.answer("⏳ Анализирую бренд и составляю концепцию...\n_Это займёт около 30 секунд_", parse_mode="Markdown")
        data = await state.get_data()
        try:
            result = await analyze_brief(data)
            await message.answer(result, parse_mode="Markdown")
            await message.answer(
                "Хочешь начать заново или изменить ответы?",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="Начать заново ✦")]],
                    resize_keyboard=True
                )
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.answer(
                "❌ Что-то пошло не так. Попробуй ещё раз — /restart\n\n"
                f"Ошибка: {str(e)[:200]}"
            )
        await state.clear()


@dp.message(StateFilter(Brief.q1))
async def ans1(message: types.Message, state: FSMContext):
    await next_question(message, state, 0, message.text)

@dp.message(StateFilter(Brief.q2))
async def ans2(message: types.Message, state: FSMContext):
    await next_question(message, state, 1, message.text)

@dp.message(StateFilter(Brief.q3))
async def ans3(message: types.Message, state: FSMContext):
    await next_question(message, state, 2, message.text)

@dp.message(StateFilter(Brief.q4))
async def ans4(message: types.Message, state: FSMContext):
    await next_question(message, state, 3, message.text)

@dp.message(StateFilter(Brief.q5))
async def ans5(message: types.Message, state: FSMContext):
    await next_question(message, state, 4, message.text)

@dp.message(StateFilter(Brief.q6))
async def ans6(message: types.Message, state: FSMContext):
    await next_question(message, state, 5, message.text)

@dp.message(StateFilter(Brief.q7))
async def ans7(message: types.Message, state: FSMContext):
    await next_question(message, state, 6, message.text)

@dp.message(StateFilter(Brief.q8))
async def ans8(message: types.Message, state: FSMContext):
    await next_question(message, state, 7, message.text)

@dp.message(StateFilter(Brief.q9))
async def ans9(message: types.Message, state: FSMContext):
    await next_question(message, state, 8, message.text)

@dp.message(StateFilter(Brief.q10))
async def ans10(message: types.Message, state: FSMContext):
    await next_question(message, state, 9, message.text)


async def main():
    async def health(request):
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info("Starting Brandboard Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
