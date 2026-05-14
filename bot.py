import asyncio
from aiogram import Bot, Dispatcher
from handlers import router

TOKEN = "8906487808:AAEC138U0mK-8tBjrWds-2FRImeVwHDi1Cw"

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


