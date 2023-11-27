import discord
import math
from discord.ext.commands import Bot

from database import Database
from config import Config


class DiscordClient(Bot):
    def __init__(self, database: Database, **kwargs):
        super().__init__(command_prefix="/", **kwargs)
        self.database = database
        self.setup_commands()

    async def on_ready(self):
        print(f"Logged in as {self.user}")

        guild = discord.Object(id=Config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

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
            parse_channels_visualization = "\n".join([f"{parse_channel[0]} -> {parse_channel[1]}" for parse_channel in page_parse_channels])
            response_content = f"**Текущие соединения** (Страница {page}, всего страниц - {total_pages}):\n\n{parse_channels_visualization}"

            await interaction.followup.send(response_content)

        @self.tree.command(name="parse-reset")
        async def parse_reset(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            self.database.drop_all_parse_channels()
            await interaction.followup.send("✅ Все соединения были успешно сброшены.")
