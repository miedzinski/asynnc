import asyncio
import logging.config
import sys

from nnc.core.bot import Bot
from nnc.core.config import Config
from nnc.core.plugin import discover_builtins


def main():
    try:
        config_path = sys.argv[1]
    except IndexError:
        config_path = 'config.toml'

    config = Config.from_toml(config_path)

    logging.config.dictConfig(config.logging)

    loop = asyncio.get_event_loop()

    bot = Bot(
        config=config,
        loop=loop,
    )

    for mod in discover_builtins():
        bot.load(mod)

    loop.create_task(bot.connect())
    loop.run_forever()
    loop.close()
