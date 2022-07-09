import os
from core.bot import Bot

if __name__ == "__main__":
    bot = Bot()
    if os.system != "nt":
        import uvloop

        uvloop.install()
    bot.run()
