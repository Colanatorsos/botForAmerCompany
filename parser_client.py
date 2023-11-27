import selfcord
import discord
import io

from database import Database
from discord_client import DiscordClient


class ParserClient(selfcord.Client):
    def __init__(self, database: Database, discord_client: DiscordClient, **kwargs):
        super().__init__(**kwargs)
        self.database = database
        self.discord_client = discord_client

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def on_message(self, message: selfcord.Message):
        if message.author.id == self.discord_client.user.id:
            return

        post_channel_ids = self.database.get_post_channel_ids(message.channel.id)

        if len(post_channel_ids) == 0:
            return

        content = message.content
        embeds = message.embeds
        files = []
        view = discord.ui.View()
        stickers = message.stickers

        for row_idx, row in enumerate(message.components):
            for component in row.children:
                if component.type != selfcord.ComponentType.button:
                    continue

                view.add_item(discord.ui.Button(
                    label=component.label,
                    disabled=component.disabled,
                    url=component.url,
                    row=row_idx
                ))

        for attachment in message.attachments:
            filename = attachment.filename
            data = io.BytesIO(await attachment.read())
            files.append(discord.File(data, filename))

        for post_channel_id in post_channel_ids:
            channel = self.discord_client.get_channel(post_channel_id[0])

            if not channel:
                print(f"Could not find post channel with ID {post_channel_id}")
                continue

            await channel.send(
                content=content,
                embeds=embeds,
                files=files,
                view=view,
                stickers=stickers,
            )
