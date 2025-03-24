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

async def get_welcome(guild_id, welcome, Type, member, guild_name):
    if Type == "channel":
        welcome_channel = await welcome.pool.fetchrow('SELECT wlc_id FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_id = welcome_channel["wlc_id"]
            welcome_channel = await welcome.bot.fetch_channel(wlc_id)
        except:
            welcome_channel = False
        return welcome_channel
    elif Type == "title":
        welcome_title = await welcome.pool.fetchrow('SELECT wlc_title FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_title = welcome_title["wlc_title"]
            welcome_title = wlc_title
        except:
            welcome_title = False
        return welcome_title
    elif Type == "hex":
        welcome_hex = await welcome.pool.fetchrow('SELECT wlc_rgb FROM info WHERE guild_id = $1', guild_id)
        wlc_hex = welcome_hex["wlc_rgb"]
        if wlc_hex is None:
            welcome_hex = discord.Color.from_rgb(1, 134, 0)
        else:
            return wlc_hex
    elif Type == "message":
        welcome_message = await welcome.pool.fetchrow('SELECT wlc_msg FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_msg = welcome_message["wlc_msg"]
            welcome_message = wlc_msg.format(user=member, mention=member.mention, server=guild_name)
        except:
            welcome_message = False
        return welcome_message
    elif Type == "image":
        welcome_image = await welcome.pool.fetchrow('SELECT wlc_pic FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_pic = welcome_image["wlc_pic"]
            welcome_image = wlc_pic
        except:
            welcome_image = False
        return welcome_image

async def get_goodbye(guild_id, goodbye, Type, member, guild_name):
    if Type == "channel":
        goodbye_channel = await goodbye.pool.fetchrow('SELECT bye_id FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_id = goodbye_channel["bye_id"]
            goodbye_channel = await goodbye.bot.fetch_channel(bye_id)
        except:
            goodbye_channel = False
        return goodbye_channel
    elif Type == "title":
        goodbye_title = await goodbye.pool.fetchrow('SELECT bye_title FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_title = goodbye_title["bye_title"]
            goodbye_title = bye_title
        except:
            goodbye_title = False
        return goodbye_title
    elif Type == "hex":
        goodbye_hex = await goodbye.pool.fetchrow('SELECT bye_rgb FROM info WHERE guild_id = $1', guild_id)
        bye_hex = goodbye_hex["bye_rgb"]
        if bye_hex is None:
            goodbye_hex = discord.Color.from_rgb(1, 134, 0)
            return goodbye_hex
        else:
            return bye_hex
        
    elif Type == "message":
        goodbye_message = await goodbye.pool.fetchrow('SELECT bye_msg FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_msg = goodbye_message["bye_msg"]
            goodbye_message = bye_msg.format(user=member, mention=member.mention, server=guild_name)
        except:
            goodbye_message = False
        return goodbye_message
    elif Type == "image":
        goodbye_image = await goodbye.pool.fetchrow('SELECT bye_pic FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_pic = goodbye_image["bye_pic"]
            goodbye_image = bye_pic
        except:
            goodbye_image = False
        return goodbye_image

class greetings(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.pool = bot.pool
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|greetings  cog loaded!|---  %s", current_time())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        guild_name = member.guild
        Type = "channel"
        channel = await get_welcome(guild_id, self, Type, member, guild_name)
        if channel:
            Type = "title"
            title = await get_welcome(guild_id, self, Type, member, guild_name)

            Type = "hex"
            hex = await get_welcome(guild_id, self, Type, member, guild_name)

            Type = "message"
            message = await get_welcome(guild_id, self, Type, member, guild_name)

            Type = "image"
            image = await get_welcome(guild_id, self, Type, member, guild_name)

            if message or title or image:
                if title:
                    welcome_embed = discord.Embed(title=title, color=discord.Color.from_str(hex))
                else:
                    welcome_embed = discord.Embed(title="", color=discord.Color.from_str(hex))      
                if message:
                    welcome_embed.add_field(name="", value=message, inline=True)
                if image:
                    welcome_embed.set_image(url=image)
                welcome_embed.set_footer(text=f"{member} ({member.id})\nUTC: {current_time()}")
                await channel.send(member.mention, embed=welcome_embed)
            
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = member.guild.id
        guild_name = member.guild
        Type = "channel"
        channel = await get_goodbye(guild_id, self, Type, member, guild_name)
        if channel == False:
            return  
        else:
            Type = "title"
            title = await get_goodbye(guild_id, self, Type, member, guild_name)

            Type = "hex"
            hex = await get_goodbye(guild_id, self, Type, member, guild_name)

            Type = "message"
            message = await get_goodbye(guild_id, self, Type, member, guild_name)

            Type = "image"
            image = await get_goodbye(guild_id, self, Type, member, guild_name)

            if message or title or image:
                if title:
                    goodbye_embed = discord.Embed(title=title, color=discord.Color.from_str(hex))
                else:
                    goodbye_embed = discord.Embed(title="", color=discord.Color.from_str(hex))
                if message:
                    goodbye_embed.add_field(name="", value=f"" + message, inline=True)
                if image:
                    goodbye_embed.set_image(url=image)
                goodbye_embed.set_footer(text=f"{member} ({member.id})\nUTC: {current_time()}")
                await channel.send(embed=goodbye_embed)

async def setup(bot):
  await bot.add_cog(greetings(bot))