import discord
import typing
import logging
import asyncio
from discord import File
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, CheckFailure
from datetime import datetime, timezone
from datetime import timedelta

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)

#Time
def current_time():
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

#Get logging channel
async def get_logging_channel(self, ctx):
    logging_channel = await self.pool.fetchrow('SELECT log_id FROM info WHERE guild_id = $1', ctx.guild.id)
    try:
        log_id = logging_channel["log_id"]
        logging_channel = await self.bot.fetch_channel(log_id)
    except:
        logging_channel = False
    return logging_channel
    
class moderation(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.pool = bot.pool
        if not hasattr(bot, 'recent_mod_actions'):
            bot.recent_mod_actions = {}

    # Register action in audit logs
    async def _register_action(self, guild_id: int, user_id: int, action: str, author_id: typing.Optional[int] = None, reason: typing.Optional[str] = None, time_val: typing.Optional[str] = None, log_channel_id: typing.Optional[int] = None, ttl: int = 8):
        try:
            now = datetime.now(timezone.utc)
            bot_store = getattr(self.bot, 'recent_mod_actions', None)
            if bot_store is None:
                self.bot.recent_mod_actions = {}
                bot_store = self.bot.recent_mod_actions

            bot_store[(int(guild_id), int(user_id))] = (action, now, author_id, reason, time_val, log_channel_id)

            asyncio.create_task(self._clear_action_after(guild_id, int(user_id), ttl))
        except Exception:
            logging.exception("_register_action failed")

    async def _clear_action_after(self, guild_id: int, user_id: int, ttl: int):
        await asyncio.sleep(ttl)
        try:
            bot_store = getattr(self.bot, 'recent_mod_actions', None)
            if bot_store is None:
                return
            bot_store.pop((guild_id, int(user_id)), None)
        except Exception:
            logging.exception("_clear_action_after failed")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|moderation cog loaded!|---   %s", current_time())
    
    # kick
    @commands.hybrid_command(name = "kick", description='Kicks a member', aliases=["Kick"])
    @commands.has_permissions(kick_members = True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, user: discord.Member|discord.User, reason: typing.Optional[str] = None):

        try:
            user_id = user.id
        except:
            user_id = int(user)
            user = await self.bot.fetch_user(int(user_id))
        server = ctx.guild.name
        author_id = ctx.author.id

        try:
            await ctx.guild.fetch_member(user_id)
        except discord.NotFound:
            await ctx.send("Unable to kick a member who's not in the server.")
        else:

            if user_id == author_id:
                await ctx.send("Trying to give yourself the boot? I mean you do you and all but like no, just no...")
            else:

                Logging_channel = await get_logging_channel(self, ctx)

                if reason == None:
                    try:
                        await user.send(f"You've been kicked from **{server}**", file=discord.File("Images/kick.gif"))
                    except discord.Forbidden:
                        pass
                    if Logging_channel == False:
                        await ctx.send(f'User {user.mention} has been kicked.\nPlease consider setting up the logging feature by running "/settings channels".')
                    else:
                        await ctx.send(f'User {user.mention} has been kicked.')

                else:
                    if ctx.interaction == None:
                        reason = " ".join(ctx.message.content.split()[2:])
                    try:
                        await user.send(f"You've been kicked from **{server}** for **{reason}**", file=discord.File("Images/kick.gif"))
                    except discord.Forbidden:
                        pass
                    if Logging_channel == False:
                        await ctx.send(f'User {user.mention} has been kicked for **{reason}**.\nPlease consider setting up the logging feature by running "/settings channels".')
                    else:
                        await ctx.send(f'User {user.mention} has been kicked for **{reason}**.')

                if Logging_channel:
                    action = "kicked"
                    time = None
                    # register so the logging cog can suppress its duplicate message
                    try:
                        await self._register_action(ctx.guild.id, user_id, action, author_id=author_id, reason=reason, time_val=time, log_channel_id=(Logging_channel.id if Logging_channel else None))
                    except Exception:
                        logging.exception("failed to register kick action")
                
                await ctx.guild.kick(user, reason=reason)

    # Ban
    @commands.hybrid_command(name = "ban", description='Bans a member', aliases=["Ban"])
    @commands.has_permissions(ban_members = True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, user: discord.Member|discord.User, reason: typing.Optional[str] = None):

        try:
            user_id = user.id
        except:
            user_id = int(user)
            user = await self.bot.fetch_user(int(user_id))
        server = ctx.guild.name
        author_id = ctx.author.id

        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:

            if user_id == author_id:
                await ctx.send("Banning yourself? Nice one but sadly I'll have to say\n# NO!")
            else:

                Logging_channel = await get_logging_channel(self, ctx)

                if reason == None:

                    try:
                        await user.send(f"You've been banned from **{server}**", file=discord.File("Images/ban.gif"))
                    except discord.Forbidden:
                        pass

                    if Logging_channel == False:
                        await ctx.send(f'User {user.mention} has been banned.\nPlease consider setting up the logging feature by running "/settings channels".')
                    else:
                        await ctx.send(f'User {user.mention} has been banned.')

                else:
                    
                    if ctx.interaction == None:
                        reason = " ".join(ctx.message.content.split()[2:])

                    try:
                        await user.send(f"You've been banned from **{server}** for **{reason}**", file=discord.File("Images/ban.gif"))
                    except discord.Forbidden:
                        pass
                    
                    if Logging_channel == False:
                        await ctx.send(f'User {user.mention} has been banned for **{reason}**.\nPlease consider setting up the logging feature by running "/settings channels".')
                    else:
                        await ctx.send(f'User {user.mention} has been banned for **{reason}**.')

                if Logging_channel:
                    action = "banned"
                    time = None
                    try:
                        # register metadata only; logging cog will create the moderation embed
                        await self._register_action(ctx.guild.id, user_id, action, author_id=author_id, reason=reason, time_val=time, log_channel_id=(Logging_channel.id if Logging_channel else None))
                    except Exception:
                        logging.exception("failed to register ban action")
                    
                await ctx.guild.ban(user, reason=reason, delete_message_days=0)

        else:
            await ctx.send("Unable to ban a user who's already banned")
   
    # Unban 
    @commands.hybrid_command(name = "unban", description='unbans a member', aliases = ["Unban","uban","Uban"])
    @commands.has_permissions(ban_members = True)
    @commands.guild_only()
    async def unban(self, ctx: commands.Context, user: discord.Member|discord.User, reason: typing.Optional[str] = None):

        try:
            user_id = user.id
        except:
            user_id = int(user)
            user = await self.bot.fetch_user(int(user_id))

        author_id = ctx.author.id

        if user_id == author_id:
            await ctx.send("Ok, let's think this over...\nYou're in the server you want to be unbanned from... right?\n-# (Buddy ain't the smartest :cold_face:)")
        else:
            try:
                await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                await ctx.send("That user is not banned in this server")
            else:

                Logging_channel = await get_logging_channel(self, ctx)

                if reason == None:
                    if Logging_channel == False:
                        await ctx.send(f'User {user.mention} has been unbanned.\nPlease consider setting up the logging feature by running "/settings channels".')
                    else:
                        await ctx.send(f'User {user.mention} has been unbanned.')

                else:
                    if ctx.interaction == None:
                        reason = " ".join(ctx.message.content.split()[2:])
                    if Logging_channel == False:
                        await ctx.send(f'User {user.mention} has been unbanned for **{reason}**.\nPlease consider setting up the logging feature by running "/settings channels".')
                    else:
                        await ctx.send(f'User {user.mention} has been unbanned for **{reason}**.')

                if Logging_channel:
                    action = "unbanned"
                    time = None
                    try:
                        await self._register_action(ctx.guild.id, user_id, action, author_id=author_id, reason=reason, time_val=time, log_channel_id=(Logging_channel.id if Logging_channel else None))
                    except Exception:
                        logging.exception("failed to register unban action")
                    
                await ctx.guild.unban(discord.Object(int(user_id)))

    # Mute 
    @commands.hybrid_command(name = "mute", description='Mutes a member', aliases = ["Mute"])
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def mute(self, ctx: commands.Context, user: discord.Member|discord.User, time: str, reason: typing.Optional[str] = None):

        try:
            user_id = user.id
        except:
            user_id = int(user)
            user = await self.bot.fetch_user(int(user_id))
        server = ctx.guild.name
        author_id = ctx.author.id

        # Validate time input
        valid_units = {"S", "M", "H", "D"}
        unit = time[-1].lower()
        duration = int(time[:-1])  

        try:
            int(duration)
        except:
            await ctx.send(f"Please insert a number")
            return
        if duration == 0:
            await ctx.send(f"Please insert a duration greater than 0")
            return
        if unit == "s":
            tdelta = timedelta(seconds=duration)
        elif unit == "m":
            tdelta = timedelta(minutes=duration)
        elif unit == "h":
            tdelta = timedelta(hours=duration)
        elif unit == "d":
            if duration < 28:
                tdelta = timedelta(days=duration)
            elif duration == 28:
                tdelta = timedelta(days=duration)
            else:
                await ctx.send("Please insert a number smaller than 29")
                return
        else:
            await ctx.send(f"Invalid time format: **{unit}**! \nValid units are: **{valid_units}**.")
            return
            
        if user_id == author_id:
            await ctx.send("Bro really just said stfu to themselves :skull:")
        else:
            Logging_channel = await get_logging_channel(self, ctx)

            if reason == None:
                try:
                    await user.send(f"You've been muted from **{server}**", file=discord.File("Images/mute.gif"))
                except discord.Forbidden:
                    pass    
                await ctx.send(f'User {user.mention} has been muted.')
            else:
                if ctx.interaction == None:
                    reason = " ".join(ctx.message.content.split()[2:])
                try:
                    await user.send(f"You've been muted from **{server}** for **{reason}**", file=discord.File("Images/mute.gif"))
                except discord.Forbidden:
                    pass
                
                await ctx.send(f'User {user.mention} has been muted for **{reason}**.')

            if Logging_channel:
                action = "muted"
                time = tdelta
                try:
                    await self._register_action(ctx.guild.id, user_id, action, author_id=author_id, reason=reason, time_val=time, log_channel_id=(Logging_channel.id if Logging_channel else None))
                except Exception:
                    logging.exception("failed to register mute action")

            try:
                member = await ctx.guild.fetch_member(user_id)
                await member.edit(timed_out_until=discord.utils.utcnow() + tdelta)
            except discord.NotFound:
                await ctx.send("Unable to mute a member who's not in the server.")

    # Unmute 
    @commands.hybrid_command(name = "unmute", description='Unmutes a member', aliases = ["Unmute", "Umute", "umute"])
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def unmute(self, ctx: commands.Context, user: discord.Member|discord.User, reason: typing.Optional[str] = None):
                
        try:
            user_id = user.id
        except:
            user_id = int(user)
            user = await self.bot.fetch_user(int(user_id))
        author_id = ctx.author.id

        if user_id == author_id:
            await ctx.send("You can't actually do that, mostly because you can't use commands when muted but also because I won't let you\n-# (and you're an idiot)")
        else:
            Logging_channel = await get_logging_channel(self, ctx)

            if reason == None:
                await ctx.send(f'User {user.mention} has been unmuted.')
            else:
                if ctx.interaction == None:
                    reason = " ".join(ctx.message.content.split()[2:])
                await ctx.send(f'User {user.mention} has been unmuted for **{reason}**.')

            if Logging_channel:
                action = "unmuted"
                time = None
                try:
                    await self._register_action(ctx.guild.id, user_id, action, author_id=author_id, reason=reason, time_val=time, log_channel_id=(Logging_channel.id if Logging_channel else None))
                except Exception:
                    logging.exception("failed to register unmute action")
            try:
                member = await ctx.guild.fetch_member(user_id)
                await member.edit(timed_out_until=None)
            except discord.NotFound:
                await ctx.send("Unable to unmute a member who's not in the server.")

    # Errors 
    @kick.error
    async def kick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("The bot is missing permissions.", ephemeral=True)
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
            return 
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return 
        else:
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error

    @ban.error
    async def ban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("The bot is missing permissions.", ephemeral=True)
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
            return 
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return 
        else:
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error

    @unban.error
    async def unban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("The bot is missing permissions.", ephemeral=True)
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
            return 
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return 
        else:
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        
    @mute.error
    async def mute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("The bot is missing permissions.", ephemeral=True)
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
            return 
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return 
        else:
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
    
    @unmute.error
    async def unmute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("The bot is missing permissions.", ephemeral=True)
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to do that :)", ephemeral=True)
            return 
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing one or more required arguments", ephemeral=True)
            return 
        else:
            await ctx.send("!!ERROR!! Please contact <@1184901953885585490>", ephemeral=True)
            logging.error("----!!ERROR!!----")
            raise error

async def setup(bot):
  await bot.add_cog(moderation(bot))