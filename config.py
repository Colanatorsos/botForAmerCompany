from os import getenv
from typing import Final


class Config:
    BOT_TOKEN: Final = getenv("BOT_TOKEN")
    SELFBOT_TOKEN: Final = getenv("SELFBOT_TOKEN")
    GUILD_ID: Final = int(getenv("GUILD_ID"))
    FINVIZ_EMAIL: Final = getenv("FINVIZ_EMAIL")
    FINVIZ_PASSWORD: Final = getenv("FINVIZ_PASSWORD")
    TRADINGVIEW_EMAIL: Final = getenv("TRADINGVIEW_EMAIL")
    TRADINGVIEW_PASSWORD: Final = getenv("TRADINGVIEW_PASSWORD")
    CHROME_BINARY_LOCATION: Final = getenv("CHROME_BINARY_LOCATION")
    CHROMEDRIVER_BINARY_LOCATION: Final = getenv("CHROMEDRIVER_BINARY_LOCATION")
