import asyncio
from Helper import HelperBot

bot = HelperBot()


async def main():
    async with bot:
        await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
