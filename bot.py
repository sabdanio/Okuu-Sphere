import asyncio
from aiogram import Bot, Dispatcher
from handlers import router

TOKEN = "8706542269:AAFxivgewbI17tlO7boF5h2-6jVgf4RhSSw"

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    try:
        dp.include_router(router)
        print("Бот запущен")
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"Bot error: {e}")


if __name__ == "__main__":
    asyncio.run(main())


