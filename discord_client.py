import discord
import math
import io

from discord.ext.commands import Bot

from database import Database
from config import Config

from datetime import datetime
from finviz_api import get_stock_data
from tradingview_parser import TradingViewParser
from news_parser import NewsParser
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# TODO: repeating code, refactor!
class TradingViewChartView(discord.ui.View):
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol

    @discord.ui.button(label="15m", style=discord.ButtonStyle.green)
    async def chart_15m(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        parser = TradingViewParser()
        image_data = parser.get_chart_screenshot_in_thread(self.symbol, 15)

        file = discord.File(io.BytesIO(image_data), "chart.png")
        await interaction.followup.send(file=file)

        parser.quit()

    @discord.ui.button(label="1h", style=discord.ButtonStyle.green)
    async def chart_1h(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        parser = TradingViewParser()
        image_data = parser.get_chart_screenshot_in_thread(self.symbol, 60)

        file = discord.File(io.BytesIO(image_data), "chart.png")
        await interaction.followup.send(file=file)

        parser.quit()

    @discord.ui.button(label="1d", style=discord.ButtonStyle.green)
    async def chart_1d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        parser = TradingViewParser()
        image_data = parser.get_chart_screenshot_in_thread(self.symbol, 1440)

        file = discord.File(io.BytesIO(image_data), "chart.png")
        await interaction.followup.send(file=file)

        parser.quit()


class DiscordClient(Bot):
    def __init__(self, database: Database, **kwargs):
        super().__init__(command_prefix="/", **kwargs)
        self.database = database
        self.parser_client = None

        self.news_parser = NewsParser()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.news_parser_task, "interval", seconds=Config.NEWS_PARSER_INTERVAL_SECONDS)
        self.scheduler.start()

        self.setup_commands()

    async def on_ready(self):
        print(f"[DiscordClient] Logged in as {self.user}")

        guild = discord.Object(id=Config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("[DiscordClient] Synced commands for the guild.")

    def setup_commands(self):
        @self.tree.command(name="add-parse-channel")
        async def add_parse_channel(interaction: discord.Interaction, post_channel_id: str, parse_channel_id: str):
            await interaction.response.defer(ephemeral=True)

            try:
                self.database.add_parse_channel(int(post_channel_id), int(parse_channel_id))
                await interaction.followup.send("✅ Канал был успешно добавлен.")
            except Exception as ex:
                print(ex)
                await interaction.followup.send("❌ Не удалось добавить канал.")

        @self.tree.command(name="remove-parse-channel")
        async def remove_parse_channel(interaction: discord.Interaction, post_channel_id: str, parse_channel_id: str):
            await interaction.response.defer(ephemeral=True)

            try:
                self.database.remove_parse_channel(int(post_channel_id), int(parse_channel_id))
                await interaction.followup.send("✅ Канал был успешно удален.")
            except Exception as ex:
                print(ex)
                await interaction.followup.send("❌ Не удалось удалить канал.")

        @self.tree.command(name="parse-list")
        async def parse_list(interaction: discord.Interaction, page: int = 1):
            if page < 1:
                return await interaction.response.send_message("❌ Неверный номер страницы.", ephemeral=True)

            await interaction.response.defer(ephemeral=True)

            ITEMS_PER_PAGE = 15

            parse_channels = self.database.get_all_parse_channels()
            page_parse_channels = parse_channels[ITEMS_PER_PAGE * (page - 1):ITEMS_PER_PAGE * page]

            if len(page_parse_channels) == 0:
                return await interaction.followup.send("❌ Эта страница пуста.")

            total_pages = math.ceil(len(parse_channels) / ITEMS_PER_PAGE)
            discord_page_parse_channels = []

            for parse_channel in parse_channels:
                discord_post_channel = self.get_channel(parse_channel[0])
                discord_parse_channel = self.parser_client.get_channel(parse_channel[1])
                discord_page_parse_channels.append((discord_post_channel, discord_parse_channel))

            parse_channels_visualization = "\n".join([
                f"**#{parse_channel[1].name}** ({parse_channel[1].id}) -> **#{parse_channel[0].name}** ({parse_channel[0].id})"
                for parse_channel in discord_page_parse_channels
            ])
            response_content = f"**Текущие соединения** (Страница {page}, всего страниц - {total_pages}):\n\n{parse_channels_visualization}"

            await interaction.followup.send(response_content)

        @self.tree.command(name="parse-reset")
        async def parse_reset(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            self.database.drop_all_parse_channels()
            await interaction.followup.send("✅ Все соединения были успешно сброшены.")

        @self.tree.command(name="stock")
        async def stock(interaction: discord.Interaction, name: str):
            await interaction.response.defer(ephemeral=True)

            data = get_stock_data(name)

            if data.get("error") == "no data":
                return await interaction.followup.send("❌ Couldn't fetch the data.")

            embed = discord.Embed(color=discord.Color.random(), timestamp=datetime.now())
            view = discord.ui.View()

            view.add_item(discord.ui.Button(label="📰 News", url=data["Last News URL"]))
            view.add_item(discord.ui.Button(label="📈 TradingView", url=data["URL"]))

            keys = [
                "Market Cap", "Price", "Avg Volume", "Shortable",
                "Shs Float", "Optionable", "Insider Own", "Inst Own",
                "Short Float / Ratio", "Target Price"
            ]

            for i in range(len(keys)):
                try:
                    embed.add_field(name=keys[i], value=data[keys[i]], inline=True)
                except Exception as ex:
                    print(f"[DiscordClient] /stock - Failed to add embed field: {ex}")

            embed.set_image(url=data["Chart URL"])

            await interaction.followup.send(embed=embed, view=view)
        
        @self.tree.command(name="future")
        @discord.app_commands.choices(
            symbol=[
                discord.app_commands.Choice(name="nq1!", value="nq1!")
            ],
            interval_time=[
                discord.app_commands.Choice(name="15m", value=15),
                discord.app_commands.Choice(name="1h", value=60),
                discord.app_commands.Choice(name="24h", value=1440)
            ]
        )
        async def future(interaction: discord.Interaction, symbol: str, interval_time: int):
            await interaction.response.defer()

            parser = TradingViewParser()
            image_data = parser.get_chart_screenshot_in_thread(symbol, interval_time)

            file = discord.File(io.BytesIO(image_data), "chart.png")
            view = TradingViewChartView(symbol)

            await interaction.followup.send(file=file, view=view)

            parser.quit()

    async def news_parser_task(self):
        parsed_news = {
            self.news_parser.parse("finviz", "quote.ashx?t=NDAQ&p=d"),
            self.news_parser.parse("benzinga", "nasdaq"),
            self.news_parser.parse("benzinga", "nasdaq-100"),
            self.news_parser.parse("ru.investing", "nq-100-news"),
            self.news_parser.parse("ru.investing", "nq-100-futures-news"),
            self.news_parser.parse("investing", "nasdaq-composite-news")
        }

        post_channel = self.get_channel(Config.NEWS_CHANNEL_ID)

        for news in parsed_news:
            if news is not None:
                await post_channel.send(news)
