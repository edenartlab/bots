import argparse
import os
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient


class MarsBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        self.set_intents(intents)
        commands.Bot.__init__(
            self,
            command_prefix="!",
            intents=intents,
        )
        self.mongo_client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.mongo_client["eden-bots-dev"]
        self.bot_commands = self.get_commands()
        print(self.bot_commands)

    def set_intents(self, intents: discord.Intents) -> None:
        intents.message_content = True
        intents.messages = True
        # if "presence" in self.metadata.intents:
        #     intents.presences = True
        # if "members" in self.metadata.intents:
        #     intents.members = True

    def get_commands(self) -> None:
        bot_data = self.db["commands"].find_one({"bot": "eden"})
        if bot_data:
            return bot_data.get("commands", [])
        else:
            return []

    async def on_ready(self) -> None:
        print(f"Running bot...")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)


def start(
    bot_name: str,
) -> None:
    print("Launching bot...")
    bot_dir = Path(__file__).parent / "bots" / bot_name
    dotenv_path = bot_dir / ".env"
    cog_paths = [f"bots.{bot_name}.{bot_name}"]
    load_dotenv(dotenv_path)

    bot = MarsBot()
    for path in cog_paths:
        res = bot.load_extension(path)
        print(res)
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarsBot")
    parser.add_argument("bot_name", help="Name of the bot to load from /bots directory")
    args = parser.parse_args()
    start(args.bot_name)
