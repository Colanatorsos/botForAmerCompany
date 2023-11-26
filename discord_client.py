import discord
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
