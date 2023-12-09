from os import getenv
from typing import Final


class Config:
    BOT_TOKEN: Final = getenv("BOT_TOKEN")
    SELFBOT_TOKEN: Final = getenv("SELFBOT_TOKEN")
    GUILD_ID: Final = int(getenv("GUILD_ID"))
    FINVIZ_AUTH_COOKIE_TOKEN: Final = getenv("FINVIZ_AUTH_COOKIE_TOKEN")
