from discord.ext import commands


class EdenCog(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        print("Hello from eden cog")

    @commands.slash_command(guild_ids=ALLOWED_GUILDS)
    async def test(self, ctx: commands.Context):
        await ctx.send("Hello from eden cog")
