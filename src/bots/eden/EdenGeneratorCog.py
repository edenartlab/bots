import asyncio
from discord.ext import commands
from cogs.CharacterGeneratorCog import CharacterGeneratorCog

class EdenCharacterGeneratorCog(CharacterGeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)
        # self.bot.loop.create_task(self.run_in_background())

    # async def run_in_background(self):
    #     await self.bot.wait_until_ready()
    #     channel = self.bot.get_channel(1006143747588898849)
    #     while not self.bot.is_closed():
    #         await channel.send("Hello, world!")
    #         await asyncio.sleep(5)  # wait for 5 seconds before sending the next message

def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenCharacterGeneratorCog(bot))