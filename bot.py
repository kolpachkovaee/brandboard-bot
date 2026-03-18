import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import config
from gemini_analyzer import analyze_brief

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.TELEGRAM_TOKEN, parse_mode="Markdown")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


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


@dp.message_handler(commands=["start", "restart"])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "✦ *Brandboard*\n\n"
        "Помогу превратить идею бренда в чёткую визуальную концепцию.\n\n"
        "Отвечу на 10 вопросов — и получишь готовый мудборд с палитрой, типографикой и образами.\n\n"
        "Нажми кнопку чтобы начать 👇",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Начать ✦")
    )


@dp.message_handler(lambda m: m.text in ["Начать ✦", "Начать заново ✦"])
async def start_brief(message: types.Message, state: FSMContext):
    await state.finish()
    await Brief.q1.set()
    await message.answer(QUESTIONS[0], reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Brief.q1)
async def ans1(message: types.Message, state: FSMContext):
    await state.update_data(brand=message.text)
    await Brief.q2.set()
    await message.answer(QUESTIONS[1])

@dp.message_handler(state=Brief.q2)
async def ans2(message: types.Message, state: FSMContext):
    await state.update_data(product=message.text)
    await Brief.q3.set()
    await message.answer(QUESTIONS[2])

@dp.message_handler(state=Brief.q3)
async def ans3(message: types.Message, state: FSMContext):
    await state.update_data(mission=message.text)
    await Brief.q4.set()
    await message.answer(QUESTIONS[3])

@dp.message_handler(state=Brief.q4)
async def ans4(message: types.Message, state: FSMContext):
    await state.update_data(audience=message.text)
    await Brief.q5.set()
    await message.answer(QUESTIONS[4])

@dp.message_handler(state=Brief.q5)
async def ans5(message: types.Message, state: FSMContext):
    await state.update_data(pain=message.text)
    await Brief.q6.set()
    await message.answer(QUESTIONS[5])

@dp.message_handler(state=Brief.q6)
async def ans6(message: types.Message, state: FSMContext):
    await state.update_data(competitors=message.text)
    await Brief.q7.set()
    await message.answer(QUESTIONS[6])

@dp.message_handler(state=Brief.q7)
async def ans7(message: types.Message, state: FSMContext):
    await state.update_data(visual_like=message.text)
    await Brief.q8.set()
    await message.answer(QUESTIONS[7])

@dp.message_handler(state=Brief.q8)
async def ans8(message: types.Message, state: FSMContext):
    await state.update_data(mood=message.text)
    await Brief.q9.set()
    await message.answer(QUESTIONS[8])

@dp.message_handler(state=Brief.q9)
async def ans9(message: types.Message, state: FSMContext):
    await state.update_data(words=message.text)
    await Brief.q10.set()
    await message.answer(QUESTIONS[9])

@dp.message_handler(state=Brief.q10)
async def ans10(message: types.Message, state: FSMContext):
    await state.update_data(person=message.text)
    await state.finish()
    await message.answer("⏳ Анализирую бренд и составляю концепцию...\n_Это займёт около 30 секунд_")
    data = await state.get_data()
    try:
        result = await analyze_brief(data)
        await message.answer(result)
        await message.answer(
            "Хочешь начать заново?",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Начать заново ✦")
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer(f"❌ Ошибка. Попробуй /restart\n\n{str(e)[:300]}")


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
    from aiogram import executor
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
