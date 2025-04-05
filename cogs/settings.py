import discord
import typing
import logging
from discord import app_commands, File
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, CheckFailure
from datetime import datetime, timezone

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)
#time
def current_time():
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

#Logging channel
async def get_logging_channel(guild_id, self):
    logging_channel = await self.pool.fetchrow('SELECT log_id FROM info WHERE guild_id = $1', guild_id)
    try:
        log_id = logging_channel["log_id"]
        logging_channel = await self.bot.fetch_channel(log_id)
    except:
        logging_channel = False
    return logging_channel

#Log entry
async def log_entry(self, author_id, guild_id, What, Type, To):
    author_name = await self.bot.fetch_user(int(author_id))
    channel = await get_logging_channel(guild_id, self)
    if channel:
        image_file = File("Images/settings_icon.png", filename="settings_icon.png")
        log_entry_embed = discord.Embed(title="Server config action!", description="Someone has made a changed a server config setting for The Holy Roller!", color=discord.Color.from_rgb(140,27,27))
        log_entry_embed.add_field(name="", value=f"**{What}** **{Type}** was changed to **{To}**")
        log_entry_embed.set_thumbnail(url="attachment://settings_icon.png") 
        if Type == "attachment":
            log_entry_embed.set_image(url=To)
        log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
        await channel.send(file=image_file, embed=log_entry_embed)
    else:
        return

class settings(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.pool = bot.pool

    group = app_commands.Group(name="settings", description="configure settings", guild_only=True)
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|settings   cog loaded!|---  %s", current_time())

# settings channels
    
    @group.command(name="channels", description="Configure channels")
    @app_commands.checks.has_permissions(administrator = True)
    async def channels(self, interaction: discord.Interaction, channel_type: typing.Literal["Logging/Logs","Welcome","Goodbye"], channel: discord.TextChannel):
        guild_id = interaction.guild.id
        if channel_type == "Logging/Logs":
            await self.pool.execute('INSERT INTO info (guild_id, log_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET log_id = $2', guild_id, channel.id)
            await interaction.response.send_message(f"**Logging channel** was changed to {channel.mention}")
            What = "Logging/Logs" 

        elif channel_type == "Welcome":
            await self.pool.execute('INSERT INTO info (guild_id, wlc_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_id = $2', guild_id, channel.id)
            await interaction.response.send_message(f"**Welcome channel** was changed to {channel.mention}")
            What = "Welcome"

        elif channel_type == "Goodbye":
            await self.pool.execute('INSERT INTO info (guild_id, bye_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_id = $2', guild_id, channel.id)
            await interaction.response.send_message(f"**Goodbye channel** was changed to {channel.mention}")
            What = "Goodbye"

        Type = "channel" 
        To = channel.mention
        author_id = interaction.user.id
        await log_entry(self, author_id, guild_id, What, Type, To)
        return

    #prefix
    @commands.command(name = "channels", aliases=["Channels", "Channel", "channel"])
    @app_commands.checks.has_permissions(administrator = True)
    async def channels_prefix(self, ctx: commands.Context, channel_type: str, channel: discord.TextChannel = None):
        channel_temp = channel_type.lower()
        channel_type = channel_temp
        guild_id = ctx.guild.id

        if channel_type in {"log", "logs", "logging", "logging/logs"}:
            channel_type = "Logging/Logs"

        elif channel_type in {"welcome", "wlc", "wel"}:
            channel_type = "Welcome"

        elif channel_type in {"goodbye", "bye", "gbye"}:
            channel_type = "Goodbye"

        else:
            await ctx.send('Invalid choice, use "help" command for assistance')
            return

        if channel_type == "Logging/Logs":
            await self.pool.execute('INSERT INTO info (guild_id, log_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET log_id = $2', guild_id, channel.id)
            await ctx.send(f"**Logging channel** was changed to {channel.mention}")
            What = "Logging/Logs" 

        elif channel_type == "Welcome":
            await self.pool.execute('INSERT INTO info (guild_id, wlc_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_id = $2', guild_id, channel.id)
            await ctx.send(f"**Welcome channel** was changed to {channel.mention}")
            What = "Welcome"

        elif channel_type == "Goodbye":
            await self.pool.execute('INSERT INTO info (guild_id, bye_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_id = $2', guild_id, channel.id)
            await ctx.send(f"**Goodbye channel** was changed to {channel.mention}")
            What = "Goodbye"
            
        Type = "channel"
        To = channel.mention
        author_id = ctx.author.id
        await log_entry(self, author_id, guild_id, What, Type, To)
        return
        

# settings message

    @group.command(name="messages", description="Configure your welcome and goodbye messages")
    @app_commands.checks.has_permissions(administrator = True)
    async def messages(self, interaction: discord.Interaction, message: typing.Literal["Welcome","Goodbye"], setting: typing.Literal["Attachment", "Title", "Message", "Color"], user_input: str):
        guild_id = interaction.guild.id
        if message == "Welcome":
            media_link = user_input
            text = user_input
            if setting == "Attachment":
                await self.pool.execute('INSERT INTO info (guild_id, wlc_pic) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_pic = $2', guild_id, media_link)  
                await interaction.response.send_message(f"**Welcome image** was changed to {media_link}")
                Type = "attachment"
                To = media_link

            elif setting == "Title":
                await self.pool.execute('INSERT INTO info (guild_id, wlc_title) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_title = $2', guild_id, text)
                await interaction.response.send_message(f"**Welcome image** was changed to {text}")
                Type = "title"
                To = text

            elif setting == "Message":
                await self.pool.execute('INSERT INTO info (guild_id, wlc_msg) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_msg = $2', guild_id, media_link)
                await interaction.response.send_message(f"**Welcome message** was changed to {text}")
                Type = "message"
                To = text

            elif setting == "Color":
                stripped_user_input = user_input.lstrip('#').replace(" ", "")
                if not len(stripped_user_input) == 6 and ',' in stripped_user_input:
                    try:
                        r, g, b = stripped_user_input.split(",")
                        r = int(r)
                        g = int(g)
                        b = int(b)
                        hex = discord.Color.from_rgb(r, g, b)
                        await self.pool.execute('INSERT INTO info (guild_id, wlc_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_rgb = $2', guild_id, str(hex))
                        await interaction.response.send_message(f"**Welcome embed color** was changed to {hex}")
                    except:
                        await interaction.response.send_message(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                        return
                elif '#' in user_input:
                    hex = user_input
                    await self.pool.execute('INSERT INTO info (guild_id, bye_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_rgb = $2', guild_id, str(user_input))
                    await interaction.response.send_message(f"**Welcome embed color** was changed to {hex}")
                else:
                    await interaction.response.send_message(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                    return
                Type = "embed color"
                To = hex

            What = "Welcome" 
            author_id = interaction.user.id
            await log_entry(self, author_id, guild_id, What, Type, To)
            return

        elif message == "Goodbye":
            media_link = user_input
            text = user_input
            if setting == "Attachment":
                await self.pool.execute('INSERT INTO info (guild_id, bye_pic) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_pic = $2', guild_id, media_link)
                await interaction.response.send_message(f"**Goodbye image** was changed to {media_link}")
                Type = "attachment"
                To = media_link

            elif setting == "Title":
                await self.pool.execute('INSERT INTO info (guild_id, bye_title) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_title = $2', guild_id, text)
                await interaction.response.send_message(f"**Goodbye image** was changed to {text}")
                Type = "title"
                To = text

            elif setting == "Message":
                await self.pool.execute('INSERT INTO info (guild_id, bye_msg) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_msg = $2', guild_id, media_link)
                await interaction.response.send_message(f"**Goodbye message** was changed to {text}")
                Type = "message"
                To = text

            elif setting == "Color":
                stripped_user_input = user_input.lstrip('#').replace(" ", "")
                if not len(stripped_user_input) == 6 and ',' in stripped_user_input:
                    try:
                        r, g, b = stripped_user_input.split(",")
                        r = int(r)
                        g = int(g)
                        b = int(b)
                        hex = discord.Color.from_rgb(r, g, b)
                        await self.pool.execute('INSERT INTO info (guild_id, wlc_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_rgb = $2', guild_id, str(hex))
                        await interaction.response.send_message(f"**Welcome embed color** was changed to {hex}")
                    except:
                        await interaction.response.send_message(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                        return
                elif '#' in user_input:
                    hex = user_input
                    await self.pool.execute('INSERT INTO info (guild_id, bye_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_rgb = $2', guild_id, str(user_input))
                    await interaction.response.send_message(f"**Welcome embed color** was changed to {hex}")
                else:
                    await interaction.response.send_message(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                    return
                Type = "embed color"
                To = hex

            What = "Goodbye"
            author_id = interaction.user.id
            await log_entry(self, author_id, guild_id, What, Type, To)
            return
        
    #prefix
    @commands.command(name = "messages", aliases=["Messages", "Message", "message"])
    @app_commands.checks.has_permissions(administrator = True)
    async def messages_prefix(self, ctx: commands.Context, message: str, setting: str, user_input: str):
        message = message.lower()
        setting = setting.lower()
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        if message == "Welcome":
            media_link = user_input
            text = user_input
            if setting == "Attachment":
                await self.pool.execute('INSERT INTO info (guild_id, wlc_pic) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_pic = $2', guild_id, media_link)  
                await ctx.send(f"**Welcome image** was changed to {media_link}")
                Type = "attachment"
                To = media_link

            elif setting == "Title":
                await self.pool.execute('INSERT INTO info (guild_id, wlc_title) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_title = $2', guild_id, text)
                await ctx.send(f"**Welcome image** was changed to {text}")
                Type = "title"
                To = text

            elif setting == "Message":
                await self.pool.execute('INSERT INTO info (guild_id, wlc_msg) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_msg = $2', guild_id, media_link)
                await ctx.send(f"**Welcome message** was changed to {text}")
                Type = "message"
                To = text

            elif setting == "Color":
                stripped_user_input = user_input.lstrip('#').replace(" ", "")
                if not len(stripped_user_input) == 6 and ',' in stripped_user_input:
                    try:
                        r, g, b = stripped_user_input.split(",")
                        r = int(r)
                        g = int(g)
                        b = int(b)
                        hex = discord.Color.from_rgb(r, g, b)
                        await self.pool.execute('INSERT INTO info (guild_id, wlc_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_rgb = $2', guild_id, str(hex))
                        await ctx.send(f"**Welcome embed color** was changed to {hex}")
                    except:
                        await ctx.send(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                        return
                elif '#' in user_input:
                    hex = user_input
                    await self.pool.execute('INSERT INTO info (guild_id, bye_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_rgb = $2', guild_id, str(user_input))
                    await ctx.send(f"**Welcome embed color** was changed to {hex}")
                else:
                    await ctx.send(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                    return
                Type = "embed color"
                To = hex

            What = "Welcome" 
            await log_entry(self, author_id, guild_id, What, Type, To)
            return

        elif message == "Goodbye":
            media_link = user_input
            text = user_input

            if setting == "Attachment":
                await self.pool.execute('INSERT INTO info (guild_id, bye_pic) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_pic = $2', guild_id, media_link)
                await ctx.send(f"**Goodbye image** was changed to {media_link}")
                Type = "attachment"
                To = media_link

            elif setting == "Title":
                await self.pool.execute('INSERT INTO info (guild_id, bye_title) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_title = $2', guild_id, text)
                await ctx.send(f"**Goodbye image** was changed to {text}")
                Type = "title"
                To = text

            elif setting == "Message":
                await self.pool.execute('INSERT INTO info (guild_id, bye_msg) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_msg = $2', guild_id, media_link)
                await ctx.send(f"**Goodbye message** was changed to {text}")
                Type = "message"
                To = text

            elif setting == "Color":
                stripped_user_input = user_input.lstrip('#').replace(" ", "")
                if not len(stripped_user_input) == 6 and ',' in stripped_user_input:
                    try:
                        r, g, b = stripped_user_input.split(",")
                        r = int(r)
                        g = int(g)
                        b = int(b)
                        hex = discord.Color.from_rgb(r, g, b)
                        await self.pool.execute('INSERT INTO info (guild_id, wlc_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_rgb = $2', guild_id, str(hex))
                        await ctx.send(f"**Welcome embed color** was changed to {hex}")
                    except:
                        await ctx.send(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                        return
                elif '#' in user_input:
                    hex = user_input
                    await self.pool.execute('INSERT INTO info (guild_id, bye_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_rgb = $2', guild_id, str(user_input))
                    await ctx.send(f"**Welcome embed color** was changed to {hex}")
                else:
                    await ctx.send(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                    return
                Type = "embed color"
                To = hex

            What = "Goodbye"
            await log_entry(self, author_id, guild_id, What, Type, To)
            return

    @group.command(name="show", description="Show current settings for the server")
    @app_commands.checks.has_permissions(administrator = True)
    async def show(self, interaction: discord.Interaction):
        setup_channels = 0
        setup_pics = 0
        guild_id = interaction.guild.id
        #Log channel
        log_id_record = await self.pool.fetchrow('SELECT log_id FROM info WHERE guild_id = $1', guild_id)
        try:
            log_id = log_id_record["log_id"]
            log_channel = await interaction.client.fetch_channel(log_id)
            setup_channels += 1
        except:
            log_channel = False
        #Welcome channel
        wlc_id_record = await self.pool.fetchrow('SELECT wlc_id FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_id = wlc_id_record["wlc_id"]
            wlc_channel = await interaction.client.fetch_channel(wlc_id)
            setup_channels += 1
        except:
            wlc_channel = False
        #Goodbye channel
        bye_id_record = await self.pool.fetchrow('SELECT bye_id FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_id = bye_id_record["bye_id"]
            bye_channel = await interaction.client.fetch_channel(bye_id)
            setup_channels += 1
        except:
            bye_channel = False
        #Welcome attachment
        wlc_pic_record = await self.pool.fetchrow('SELECT wlc_pic FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_pic = wlc_pic_record["wlc_pic"]
            if wlc_pic != None and wlc_pic.lower() != "none":
                setup_pics += 1
        except:
            wlc_pic = False
        #Goodbye attachment
        bye_pic_record = await self.pool.fetchrow('SELECT bye_pic FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_pic = bye_pic_record["bye_pic"]
            if bye_pic != None and bye_pic.lower() != "none":
                setup_pics += 1
        except:
            bye_pic = False
        #Embed
        show_embed = discord.Embed(title="Server settings", color=discord.Color.from_rgb(41,134,0))
        if setup_channels > 0:
            if log_channel == False:
                show_embed.add_field(name="Logging channel:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Logging channel:", value=log_channel.mention, inline=False)
            if wlc_channel == False:
                show_embed.add_field(name="Welcome channel:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Welcome channel:", value=wlc_channel.mention, inline=False)
            if bye_channel == False:
                show_embed.add_field(name="Goodbye channel:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Goodbye channel:", value=bye_channel.mention, inline=False)
        else:
            show_embed.add_field(name="No channels have been set", value='Please run "/settings channels" to finish setting up your channels', inline=False)

        if setup_pics > 0:           
            if wlc_pic == False:
                show_embed.add_field(name="Welcome attachment:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Welcome attachment:", value=wlc_pic, inline=False)

            if bye_pic == False:
                show_embed.add_field(name="Goodbye attachment:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Goodbye attachment:", value=bye_pic, inline=False)
        else:
            show_embed.add_field(name="No attachments have been set", value='Please run "/settings attachments" to finish setting up your attachments.', inline=False)
        #Embed send
        show_embed.set_footer(text=f"{setup_channels}/3 channels set\n{setup_pics}/2 attachments set\nUTC: {current_time()}")
        await interaction.response.send_message(embed=show_embed)
        return

    #prefix
    @commands.command(name = "show", aliases=["Show"])
    @app_commands.checks.has_permissions(administrator = True)
    async def show_prefix(self, ctx: commands.Context):
        setup_channels = 0
        setup_pics = 0
        guild_id = ctx.guild.id
        #Log channel
        log_id_record = await self.pool.fetchrow('SELECT log_id FROM info WHERE guild_id = $1', guild_id)
        try:
            log_id = log_id_record["log_id"]
            log_channel = await self.bot.fetch_channel(log_id)
            setup_channels += 1
        except:
            log_channel = False
        #Welcome channel
        wlc_id_record = await self.pool.fetchrow('SELECT wlc_id FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_id = wlc_id_record["wlc_id"]
            wlc_channel = await self.bot.fetch_channel(wlc_id)
            setup_channels += 1
        except:
            wlc_channel = False
        #Goodbye channel
        bye_id_record = await self.pool.fetchrow('SELECT bye_id FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_id = bye_id_record["bye_id"]
            bye_channel = await self.bot.fetch_channel(bye_id)
            setup_channels += 1
        except:
            bye_channel = False
        #Welcome attachment
        wlc_pic_record = await self.pool.fetchrow('SELECT wlc_pic FROM info WHERE guild_id = $1', guild_id)
        try:
            wlc_pic = wlc_pic_record["wlc_pic"]
            if wlc_pic != None and wlc_pic.lower() != "none":
                setup_pics += 1
        except:
            wlc_pic = False
        #Goodbye attachment
        bye_pic_record = await self.pool.fetchrow('SELECT bye_pic FROM info WHERE guild_id = $1', guild_id)
        try:
            bye_pic = bye_pic_record["bye_pic"]
            if bye_pic != None and bye_pic.lower() != "none":
                setup_pics += 1
        except:
            bye_pic = False
        #Embed
        show_embed = discord.Embed(title="Server settings", color=discord.Color.from_rgb(41,134,0))
        if setup_channels > 0:
            if log_channel == False:
                show_embed.add_field(name="Logging channel:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Logging channel:", value=log_channel.mention, inline=False)

            if wlc_channel == False:
                show_embed.add_field(name="Welcome channel:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Welcome channel:", value=wlc_channel.mention, inline=False)

            if bye_channel == False:
                show_embed.add_field(name="Goodbye channel:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Goodbye channel:", value=bye_channel.mention, inline=False)
        else:
            show_embed.add_field(name="No channels have been set", value='Please run "/settings channels" to finish setting up your channels', inline=False)

        if setup_pics > 0:           
            if wlc_pic == False:
                show_embed.add_field(name="Welcome attachment:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Welcome attachment:", value=wlc_pic, inline=False)
            if bye_pic == False:
                show_embed.add_field(name="Goodbye attachment:", value="**Not set**", inline=False)
            else:
                show_embed.add_field(name="Goodbye attachment:", value=bye_pic, inline=False)
        else:
            show_embed.add_field(name="No attachments have been set", value='Please run "/settings attachments" to finish setting up your attachments.', inline=False)
        #Embed send
        show_embed.set_footer(text=f"{setup_channels}/3 channels set\n{setup_pics}/2 attachments set\nUTC: {current_time()}")
        await ctx.send(embed=show_embed)
        return

    @channels.error
    async def channels_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permissions to do that :)", ephemeral=True)    
    
    @channels_prefix.error
    async def channels_prefix_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True) 

    @messages.error
    async def messages_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permissions to do that :)", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("You're missing one or more required arguments", ephemeral=True)
            return    
        
    @messages_prefix.error
    async def messages_prefix_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return    

    @show.error
    async def show_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        
    @show_prefix.error
    async def show_prefix_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error

async def setup(bot):
  await bot.add_cog(settings(bot))