import discord
import discord.ext.commands
import os
import asyncio
import asyncpg
import logging
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from time import perf_counter
from asyncpg.pool import create_pool

from apikeys import Token, Database_Name, Host_IP, Host_Port, User_Name, User_Pass

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)

DEFAULT_PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

#   time
def current_time ():
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

async def get_server_prefix(bot, message):
    prefix_record = await bot.pool.fetchrow('SELECT prefix FROM info WHERE guild_id = $1', message.guild.id)
    prefix = prefix_record["prefix"]
    return prefix

bot = commands.Bot(command_prefix= get_server_prefix, help_command=None, intents=intents)

##  Events

    #  on_guild_join
@bot.event
async def on_guild_join(guild):
    owner = guild.owner
    server = guild.name
    await owner.send(f"Thank you for adding The Holy Roller to **{server}**")
    await bot.pool.execute('INSERT INTO info (guild_id, prefix) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET prefix = $2', guild.id, DEFAULT_PREFIX)

    #  on_guild_remove
@bot.event
async def on_guild_remove(guild):
    await bot.pool.execute('DELETE FROM info WHERE guild_id = $1', guild.id)
    
##  Commands

#   Change prefix 
@bot.hybrid_command(name = "prefix", description='Change prefix used for the bot in this server', aliases=["Prefix"])
@commands.has_permissions(manage_guild = True)
async def setprefix(ctx: commands.Context, prefix: str):
    try:
        await bot.pool.execute('UPDATE info SET prefix = $2 WHERE guild_id = $1', ctx.guild.id, prefix)
        await ctx.send(f"Changed prefix to {prefix}")
    except:
        await ctx.send("Could not change prefix, please try again")

#   Error handling
@setprefix.error
async def setprefix_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("There was an error executing this command, please contact developer")
        logging.error("----!!ERROR!!----")
        raise error
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permissions to do that :)", ephemeral=True)
        return 
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You're missing one or more required arguments", ephemeral=True)
        return 
    else:
        await ctx.send("There was an error executing this command, please contact developer")
        logging.error("----!!ERROR!!----")
        raise error

##  Core

#  on_ready
@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    logging.info(f"synced %s command(s)", len(synced))
    await bot.change_presence(activity=discord.activity.Game(name="Church service simulator 2024"))
    logging.info("The Holly Roller is awake and high as a fucking kite just like always     UTC:%s\n", current_time())
    
#  Load cogs
async def load():
    start = perf_counter()
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    end = perf_counter()
    logging.info(f"Loading took %s ms", (end-start)*1000)

async def connect():
    try:
        bot.pool = await asyncpg.create_pool(database=Database_Name, host=Host_IP, port=Host_Port, user=User_Name, password=User_Pass)
        logging.info("Connection to DB was successfully established.")
        return True
    except:
        logging.critical("Connection to DB failed to establish.")
        return False

#  Main
async def main():

    #startup debugging, remove # to turn on
    #discord.utils.setup_logging()

    connected = False
    while connected == False:
        connected = await connect()

    #Start
    try:
        await load()
        await bot.start(Token)
    finally:
        await bot.pool.close()

asyncio.run(main())