import discord
import typing
import logging
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)

#time
def current_time ():
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

def help_embed(self):
    embed = discord.Embed(title="Help", description="This is a list of different commands and what they do.", color=660091)

    embed.set_author(name="Local Drug Lord", icon_url='attachment://LDL_pfp.png')
    embed.set_thumbnail(url='attachment://Holy_Roller_pfp.png')

    embed.add_field(name="**---| Moderation |---**", value= "", inline=False)
    embed.add_field(name="*/ban*", value="bans a member.", inline=True)
    embed.add_field(name="*/kick*", value="Kicks a member.", inline=True)
    embed.add_field(name="*/mute*", value="mutes a member.", inline=True)
    embed.add_field(name="*/unban*", value="unbans a member.", inline=True)
    embed.add_field(name="*/unmute*", value="unmutes a member.", inline=True)

    embed.add_field(name="**---| Other      |---**", value="", inline=False)
    embed.add_field(name="*/help*", value="Shows this message, use /help settings for help with settings.", inline=True)
    embed.add_field(name="*/ping*", value="Shows the response time of the bot.", inline=True)
    embed.set_footer(text=f"UTC: {current_time()}")

    return embed

def settings_help_embed(self):
    embed = discord.Embed(title="Help", description="This is a list of different commands and what they do.\n**Note that all settings except the HEX values has to be set up for the welcome/goodbye messages to send.**", color=660091)
    embed.set_author(name="Local Drug Lord", icon_url='attachment://LDL_pfp.png')
    embed.set_thumbnail(url='attachment://Holy_Roller_pfp.png')

    embed.add_field(name="**---| Channel    |---**", value= "", inline=False)
    embed.add_field(name="*/Settings show*", value="Show the servers current channel config", inline=True)
    embed.add_field(name="*/Settings channel*", value="This command is used to change what channels does what. \nCurrent options are:", inline=True)
    embed.add_field(name="*Logging/Logs*", value= "This is what channel to use for keeping logs.", inline=True)
    embed.add_field(name="*Welcome*", value= "This is what channel to use for the welcome message.", inline=True)
    embed.add_field(name="*Goodbye*", value= "This is what channel to use for the goodbye message.", inline=True)

    embed.add_field(name="**---| Delete    |---**", value= "", inline=False)
    embed.add_field(name="*/Settings delete*", value="This command is used to delete settings like channels or prefix, you can also fully reset everything channel related back to default", inline=True)
    embed.add_field(name="*/Settings delete_message*", value="This command does the same as /Settings delete but for messages, this also has a reset feature but for messages", inline=True)

    embed.add_field(name="**---| Messages   |---**", value= "", inline=False)
    embed.add_field(name="*/Settings messages*", value="Configure the welcome and goodbye embed messages. \nCurrent settings are:", inline=True)
    embed.add_field(name="*Attachment*", value= "This is the image you want to send in the message.\n(This should be in the form of a url/media link)", inline=True)
    embed.add_field(name="*Title*", value= "This is the title for your embed message.", inline=True)
    embed.add_field(name="*Message*", value= 'This is the content of the message, for help with formatting look at "Formatting" section.', inline=True)
    embed.add_field(name="*Color*", value= "This is what color should be used for the embed.\n**Note: This should be in the HEX or RGB format**", inline=True)

    embed.add_field(name="**---| Formatting |---**", value= "", inline=False)
    embed.add_field(name="*This is a small tutorial on how to format your messages*", value="", inline=False)
    embed.add_field(name="", value='**{user}** or **{member}**:\nThese placeholders insert the username of the person joining/leaving.\n(e.g., "Hello {user}!" becomes "Hello discord_user123!")', inline=True)
    embed.add_field(name="", value='**{mention}**:\nThis inserts a mention of the user, including the "@" symbol.\n(e.g., "Hello {mention}!" becomes "Hello @discord_user123!")', inline=True)
    embed.add_field(name="", value='**{server}**:\nThis inserts the name of the server the user joined/left.\n(e.g., "Welcome to {server}!" becomes "Welcome to Cool Chat")', inline=True)

    embed.set_footer(text=f"UTC: {current_time()}")

    return embed

class help(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|Help       cog loaded!|---  %s", current_time())

    @app_commands.command(name="help", description="command help list")
    async def help(self, interaction: discord.Integration, category: typing.Literal["all/general","settings"] = "all/general"):

        file1 = discord.File('Images/Holy_Roller_pfp.png')
        file2 = discord.File('Images/LDL_pfp.png')
        
        if category == "settings":
            embed = settings_help_embed(self)
        else:
            embed = help_embed(self)

        await interaction.response.send_message(files=[file1, file2], embed=embed)

    @commands.command(name="help", aliases=["Help", "H", "h"])
    async def help_prefix(self, ctx: commands.Context, category: typing.Optional[str] = "all/general"):

        category = category.lower()
        file1 = discord.File('Images/Holy_Roller_pfp.png')
        file2 = discord.File('Images/LDL_pfp.png')
        
        if category in {"settings", "setting" ,"s", "conf", "configure", "configuration"}:
            embed = settings_help_embed(self)
        else:
            embed = help_embed(self)

        await ctx.send(files=[file1, file2], embed=embed)

    @help.error
    async def help_error(self, interaction: discord.Integration, error):
        await interaction.response.send_message("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
        logging.error("----!!ERROR!!----")
        raise error
    
    @help_prefix.error
    async def help_prefix_error(self, ctx: commands.Context, error):
        await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
        logging.error("----!!ERROR!!----")
        raise error

async def setup(bot):
    await bot.add_cog(help(bot))