"""Скрипт для удаления webhook"""
import asyncio
from aiogram import Bot
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    
    try:
        # Получить информацию о webhook
        webhook_info = await bot.get_webhook_info()
        print(f"Current webhook: {webhook_info.url if webhook_info.url else 'None'}")
        
        if webhook_info.url:
            # Удалить webhook
            await bot.delete_webhook(drop_pending_updates=True)
            print("OK: Webhook deleted!")
        else:
            print("OK: No webhook set")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
