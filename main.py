import discord
import logging
import asyncio
import traceback

from config import Config
from database import Database

from parser_client import ParserClient
from discord_client import DiscordClient

from finviz_api import login_finviz
from tradingview_parser import TradingViewParser

logging.basicConfig(level=logging.INFO)


async def main():
    database = Database("database.sqlite3")

    discord_client = DiscordClient(database, intents=discord.Intents.default())
    parser_client = ParserClient(database, discord_client)
    discord_client.parser_client = parser_client

    try:
        login_finviz()
        print("[DiscordClient] Logged in Finviz")
    except Exception as ex:
        print("[DiscordClient] Failed to log in Finviz")
        print(ex)

    try:
        parser = TradingViewParser()
        parser.log_in(Config.TRADINGVIEW_EMAIL, Config.TRADINGVIEW_PASSWORD)
        parser.quit()
    except Exception as ex:
        print("[DiscordClient] Failed to log in TradingView")
        print(traceback.format_exc())

    await asyncio.gather(
        parser_client.start(Config.SELFBOT_TOKEN),
        discord_client.start(Config.BOT_TOKEN)
    )

    database.close()


if __name__ == "__main__":
    asyncio.run(main())
