import discord
import math
import asyncio

from discord.ext.commands import Bot

from database import Database
from config import Config

from datetime import datetime
from finviz_api import login_finviz, get_stock_data


class DiscordClient(Bot):
    def __init__(self, database: Database, **kwargs):
        super().__init__(command_prefix="/", **kwargs)
        self.database = database
        self.parser_client = None
        self.setup_commands()

    async def on_ready(self):
        print(f"Logged in as {self.user}")

        try:
            login_finviz()
            print("Logged in Finviz.")
        except Exception as ex:
            print(ex)
            print("Failed to log in Finviz.")

        guild = discord.Object(id=Config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Synced commands for the guild.")

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

            keys = [
                "Market Cap", "Price", "Avg Volume", "Shortable",
                "Shs Float", "Optionable", "Insider Own", "Inst Own",
                "Short Float / Ratio", "Target Price"
            ]

            for i in range(len(keys)):
                embed.add_field(name=keys[i], value=data[keys[i]], inline=True)

            embed.set_image(url=data["Chart URL"])

            await interaction.followup.send(embed=embed)
