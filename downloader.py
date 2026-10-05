from datetime import datetime
import disnake

from database.opt_out import OptOutDb
from utils import get_db, prep_msg, prep_emoji


class Downloader:
    server_id: int
    database_file: str
    bot: str

    def __init__(self, bot: str, server_id: int, database_file: str):
        self.bot = bot
        self.server_id = server_id
        self.database_file = database_file

    async def run(
        self, filters: set[str] | None, from_date: datetime, to_date: datetime
    ):
        intents = disnake.Intents.default()
        intents.message_content = True
        client = disnake.Client(intents=intents)

        @client.event
        async def on_ready():
            try:
                await self.download(client, filters, from_date, to_date)
            finally:
                await client.close()

        try:
            await client.start(self.bot)
        except disnake.LoginFailure:
            print("Invalid bot token")
        except disnake.PrivilegedIntentsRequired:
            print("Message Content Intent is required")
        finally:
            await client.close()
            await client.http.close()

    async def download(
        self,
        client: disnake.Client,
        filters: set[str] | None,
        from_date: datetime,
        to_date: datetime,
    ):
        server = client.get_guild(self.server_id)
        if server is None:
            print("Server not found")
            return

        opted_out = set(OptOutDb.get_all())
        database = get_db(self.database_file)
        cursor = database.cursor()

        for channel in server.text_channels:
            # filter channels
            if filters is not None and not any(
                part in channel.name.casefold() for part in filters
            ):
                continue

            # check permissions
            perms = channel.permissions_for(server.me)
            if not perms.view_channel or not perms.read_message_history:
                print(f"Missing permissions in {channel.name}")
                continue

            try:
                async for message in channel.history(
                    limit=None, after=from_date, before=to_date
                ):
                    # filter out opted-out users
                    if str(message.author.id) in opted_out:
                        continue

                    # system messages
                    if message.type not in (
                        disnake.MessageType.default,
                        disnake.MessageType.reply,
                    ):
                        continue

                    # bots
                    if message.author.bot:
                        continue

                    msg = prep_msg(message.content or "")

                    # stickers
                    if message.stickers:
                        for sticker in message.stickers:
                            msg += f" <sticker>{sticker.name}</sticker>"

                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO messages (channel, date, text)
                        VALUES (?, ?, ?)
                        """,
                        (channel.name, message.created_at.isoformat(), msg),
                    )
                    if cursor.rowcount == 0:
                        continue

                    message_id = cursor.lastrowid
                    for reaction in message.reactions:
                        reaction_count = reaction.count
                        async for user in reaction.users(limit=None):
                            if str(user.id) in opted_out:
                                reaction_count -= 1

                        if reaction_count <= 0:
                            continue

                        cursor.execute(
                            """
                            INSERT INTO reactions (message_id, reaction, count)
                            VALUES (?, ?, ?)
                            """,
                            (
                                message_id,
                                prep_emoji(str(reaction.emoji)),
                                reaction_count,
                            ),
                        )
                database.commit()

            except disnake.Forbidden:
                print(f"Forbidden: {channel.name}")
                database.rollback()
                continue
            except Exception as e:
                print(f"Error downloading messages in {channel.name}: {e}")
                database.rollback()
                continue

        database.close()
        print("Download finished")
