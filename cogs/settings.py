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
        log_entry_embed = discord.Embed(title="Server config action!", description="Someone has made a changed a server config for The Holy Roller!", color=discord.Color.from_rgb(140,27,27))
        log_entry_embed.add_field(name="", value=f"**{What}** **{Type}** was changed to **{To}**")
        log_entry_embed.set_thumbnail(url="attachment://settings_icon.png") 
        if Type == "attachment":
            log_entry_embed.set_image(url=To)
        log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
        await channel.send(file=image_file, embed=log_entry_embed)
    else:
        return
    
async def delete_log_entry(self, author_id, guild_id, message_type, setting):
    author_name = await self.bot.fetch_user(int(author_id))
    channel = await get_logging_channel(guild_id, self)
    if channel:
        image_file = File("Images/settings_icon.png", filename="settings_icon.png")
        log_entry_embed = discord.Embed(title="Server config action!", description="Someone has made a changed a server config for The Holy Roller!", color=discord.Color.from_rgb(140,27,27))
        log_entry_embed.set_thumbnail(url="attachment://settings_icon.png") 
        if message_type == None:
            if setting == "All":
                log_entry_embed.add_field(name="", value="**All** channel settings have been deleted for this server.")
            else:
                log_entry_embed.add_field(name="", value=f"**{setting}** channel setting have been deleted for this server.", inline=False)
        else:
            if setting == "All":
                log_entry_embed.add_field(name="", value=f"**All {message_type}** message settings have been deleted for this server.")
            elif message_type == "Attachment":
                log_entry_embed.add_field(name="", value=f"**{message_type} {setting}** message setting have been deleted for this server.")
            else:
                log_entry_embed.add_field(name="", value=f"**{message_type} {setting}** message setting have been deleted for this server.")
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

        if channel_type.lower() in {"log", "logs", "logging", "logging/logs"}:
            channel_type = "Logging/Logs"

        elif channel_type.lower() in {"welcome", "wlc", "wel"}:
            channel_type = "Welcome"

        elif channel_type.lower() in {"goodbye", "bye", "gbye"}:
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
                    await self.pool.execute('INSERT INTO info (guild_id, wlc_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET wlc_rgb = $2', guild_id, str(user_input))
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
                        await self.pool.execute('INSERT INTO info (guild_id, bye_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_rgb = $2', guild_id, str(hex))
                        await interaction.response.send_message(f"**Goodbye embed color** was changed to {hex}")
                    except:
                        await interaction.response.send_message(f"`{user_input}` is not a valid rgb or hex code, please use rgb or hex")
                        return
                elif '#' in user_input:
                    hex = user_input
                    await self.pool.execute('INSERT INTO info (guild_id, bye_rgb) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET bye_rgb = $2', guild_id, str(user_input))
                    await interaction.response.send_message(f"**Goodbye embed color** was changed to {hex}")
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

    #delete
    @group.command(name="delete", description="Delete/reset a specific setting or all settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete(self, interaction: discord.Interaction, setting: typing.Literal["Logging/Logs", "Welcome_channel", "Goodbye_channel", "Prefix", "All"]):
        guild_id = interaction.guild.id
        author_id = interaction.user.id
        await delete_log_entry(self, author_id, guild_id, None, setting)
        if setting == "Logging/Logs":
            await self.pool.execute('UPDATE info SET log_id = NULL WHERE guild_id = $1', guild_id)
            await interaction.response.send_message("Logging channel setting has been reset.")
        elif setting == "Welcome":
            await self.pool.execute('UPDATE info SET wlc_id = NULL WHERE guild_id = $1', guild_id)
            await interaction.response.send_message("Welcome channel setting have been reset.")
        elif setting == "Goodbye":
            await self.pool.execute('UPDATE info SET bye_id = NULL WHERE guild_id = $1', guild_id)
            await interaction.response.send_message("Goodbye channel setting have been reset.")
        elif setting == "Prefix":
            await self.pool.execute('UPDATE info SET prefix = $1 WHERE guild_id = $2', '!', guild_id)
            await interaction.response.send_message('Prefix setting has been reset to default (!).')
        elif setting == "All":
            await self.pool.execute('UPDATE info SET log_id = NULL, wlc_id = NULL, bye_id = NULL, prefix = $1 WHERE guild_id = $2', '!', guild_id)
            await interaction.response.send_message("All channel settings have been deleted for this server.")
        return

    #Prefix
    @commands.command(name="delete", aliases=["reset"])
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_prefix(self, ctx: commands.Context, setting: str):
        guild_id = ctx.guild.id
        author_id = ctx.author.id
        setting = setting.lower()
        await delete_log_entry (self, author_id, guild_id, None, setting)
        if setting in {"logging", "logs", "log"}:
            await self.pool.execute('UPDATE info SET log_id = NULL WHERE guild_id = $1', guild_id)
            await ctx.send("Logging channel setting has been reset.")
        elif setting in {"welcome", "wlc"}:
            await self.pool.execute('UPDATE info SET wlc_id = NULL WHERE guild_id = $1', guild_id)
            await ctx.send("Welcome channel setting have been reset.")
        elif setting in {"goodbye", "bye"}:
            await self.pool.execute('UPDATE info SET bye_id = NULL WHERE guild_id = $1', guild_id)
            await ctx.send("Goodbye channel setting have been reset.")
        elif setting in {"prefix"}:
            await self.pool.execute('UPDATE info SET prefix = $1 WHERE guild_id = $2', '!', guild_id)
            await ctx.send('Prefix setting has been reset to default (!).')
        elif setting == "all":
            await self.pool.execute('UPDATE info SET log_id = NULL, wlc_id = NULL, bye_id = NULL, prefix = $1 WHERE guild_id = $2', '!', guild_id)
            await ctx.send("All channel setting have been deleted for this server.")
        else:
            await ctx.send("Invalid setting. Use logging, welcome, goodbye, prefix, or all.")
        return

    #Delete_message
    @group.command(name="delete_message", description="Delete/reset message settings (content, color, etc.)")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_message(self, interaction: discord.Interaction, message_type: typing.Literal["Welcome", "Goodbye"], setting: typing.Literal["Attachment", "Title", "Message", "Color", "All"]):
        guild_id = interaction.guild.id
        author_id = interaction.user.id
        await delete_log_entry(self, author_id, guild_id, message_type, setting)
        if message_type == "Welcome":
            if setting == "Attachment":
                await self.pool.execute('UPDATE info SET wlc_pic = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Welcome image has been reset.")
            elif setting == "Title":
                await self.pool.execute('UPDATE info SET wlc_title = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Welcome title has been reset.")
            elif setting == "Message":
                await self.pool.execute('UPDATE info SET wlc_msg = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Welcome message has been reset.")
            elif setting == "Color":
                await self.pool.execute('UPDATE info SET wlc_rgb = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Welcome color has been reset.")
            elif setting == "All":
                await self.pool.execute('UPDATE info SET wlc_pic = NULL, wlc_title = NULL, wlc_msg = NULL, wlc_rgb = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("All welcome message settings have been reset.")
        elif message_type == "Goodbye":
            if setting == "Attachment":
                await self.pool.execute('UPDATE info SET bye_pic = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Goodbye image has been reset.")
            elif setting == "Title":
                await self.pool.execute('UPDATE info SET bye_title = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Goodbye title has been reset.")
            elif setting == "Message":
                await self.pool.execute('UPDATE info SET bye_msg = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Goodbye message has been reset.")
            elif setting == "Color":
                await self.pool.execute('UPDATE info SET bye_rgb = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("Goodbye color has been reset.")
            elif setting == "All":
                await self.pool.execute('UPDATE info SET bye_pic = NULL, bye_title = NULL, bye_msg = NULL, bye_rgb = NULL WHERE guild_id = $1', guild_id)
                await interaction.response.send_message("All goodbye message settings have been reset.")
        else:
            await interaction.response.send_message("Invalid choice.", ephemeral=True)
        return
    
    #Prefix
    @commands.command(name="delete_message", aliases=["reset_message"])
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_message_prefix(self, ctx: commands.Context, message_type: str, setting: str):
        guild_id = ctx.guild.id
        author_id = ctx.author.id
        message_type = message_type.lower()
        setting = setting.lower()
        await delete_log_entry(self, author_id, guild_id, message_type, setting)
        if message_type in {"welcome", "wlc"}:
            if setting == "attachment":
                await self.pool.execute('UPDATE info SET wlc_pic = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Welcome image has been reset.")
            elif setting == "title":
                await self.pool.execute('UPDATE info SET wlc_title = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Welcome title has been reset.")
            elif setting == "message":
                await self.pool.execute('UPDATE info SET wlc_msg = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Welcome message has been reset.")
            elif setting == "color":
                await self.pool.execute('UPDATE info SET wlc_rgb = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Welcome color has been reset.")
            elif setting == "all":
                await self.pool.execute('UPDATE info SET wlc_pic = NULL, wlc_title = NULL, wlc_msg = NULL, wlc_rgb = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("All welcome message settings have been reset.")
        elif message_type in {"goodbye", "bye"}:
            if setting == "attachment":
                await self.pool.execute('UPDATE info SET bye_pic = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Goodbye image has been reset.")
            elif setting == "title":
                await self.pool.execute('UPDATE info SET bye_title = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Goodbye title has been reset.")
            elif setting == "message":
                await self.pool.execute('UPDATE info SET bye_msg = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Goodbye message has been reset.")
            elif setting == "color":
                await self.pool.execute('UPDATE info SET bye_rgb = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("Goodbye color has been reset.")
            elif setting == "all":
                await self.pool.execute('UPDATE info SET bye_pic = NULL, bye_title = NULL, bye_msg = NULL, bye_rgb = NULL WHERE guild_id = $1', guild_id)
                await ctx.send("All goodbye message settings have been reset.")
        else:
            await ctx.send("Invalid choice. Use welcome/goodbye and attachment/title/message/color/all.")
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

    @delete.error
    async def delete_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permissions to do that :)", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("You're missing one or more required arguments", ephemeral=True)
            return  
        
    @delete_prefix.error
    async def delete_prefix_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return  
        
    @delete_message.error
    async def delete_message_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permissions to do that :)", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("You're missing one or more required arguments", ephemeral=True)
            return  
        
    @delete_message_prefix.error
    async def delete_message_prefix_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, app_commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return  

async def setup(bot):
  await bot.add_cog(settings(bot))