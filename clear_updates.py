import asyncio
from aiogram import Bot

BOT_TOKEN = "8573719664:AAF1FYleLXiKWxxz9MsP--cn5zGQ92ySefg"

async def main():
    bot = Bot(token=BOT_TOKEN)
    updates = await bot.get_updates(limit=100)
    if updates:
        last_id = updates[-1].update_id
        await bot.get_updates(offset=last_id + 1)
    await bot.session.close()
    print("Старые апдейты очищены!")

if __name__ == "__main__":
    asyncio.run(main())
