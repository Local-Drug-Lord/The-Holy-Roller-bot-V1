import discord
import logging
from discord.ext import commands
from datetime import datetime, timezone

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)
#time
def current_time ():
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

class request(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.pool = bot.pool
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|Request    cog loaded!|---  %s", current_time())

    @commands.hybrid_command(name="request", description="Request a feature", aliases=["Request"])
    async def ping(self, ctx: commands.Context):
        Issue_embed = discord.Embed(title="Request a feature :tools:", color=discord.Color.from_rgb(41,134,0))
        Issue_embed.add_field(name="Github request:", value= "https://github.com/Local-Drug-Lord/The-Holy-Roller-bot-V1/issues/new/choose", inline=False)

        Issue_embed.set_footer(text=f"UTC: {current_time()}")
        await ctx.send(embed=Issue_embed)

    @ping.error
    async def ping_error(self, ctx: commands.Context, error):
        await ctx.send("There was an error executing this command, please contact developer")
        logging.error("----!!ERROR!!----")
        raise error 

async def setup(bot):
  await bot.add_cog(request(bot))