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

class ping(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.pool = bot.pool
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|Ping       cog loaded!|---  %s", current_time())

    @commands.hybrid_command(name="ping", description="you ping i pong! ;)", aliases=["Ping"])
    async def ping(self, ctx: commands.Context):
        bot_latency = round(self.bot.latency * 1000)
        Ping_embed = discord.Embed(title="Pong! :ping_pong:", color=discord.Color.from_rgb(41,134,0))
        Ping_embed.add_field(name=":satellite: API:", value= f"**{bot_latency} ms.**", inline=False)

        try:
            await self.pool.fetchrow('SELECT guild_id FROM info') #WHERE guild_id = $1', ctx.guild.id )
            Ping_embed.add_field(name=":file_cabinet: Database:", value= "**DB connection: __Normal__**", inline=False)
        except:
            Ping_embed.add_field(name=":file_cabinet: Database:", value= "**DB connection: __Dead__**", inline=False)
        Ping_embed.set_footer(text=f"UTC: {current_time()}")
        await ctx.send(embed=Ping_embed)

    @ping.error
    async def ping_error(self, ctx: commands.Context, error):
        await ctx.send("There was an error executing this command, please contact developer")
        logging.error("----!!ERROR!!----")
        raise error 

async def setup(bot):
  await bot.add_cog(ping(bot))