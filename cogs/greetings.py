import discord
import logging
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import re

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)

# ============== RAID LOGIC ==============
# Dictionary to track join timestamps per guild for raid detection
raid_join_tracker = {}
# Raid detection thresholds (hardcoded)
RAID_JOIN_THRESHOLD = 4  # Number of joins to trigger alert
RAID_DETECTION_WINDOW = 2  # Seconds window for threshold
# ========================================

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
        welcome_hex = await welcome.pool.fetchrow('SELECT wlc_hex FROM info WHERE guild_id = $1', guild_id)
        wlc_hex = welcome_hex["wlc_hex"]
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
        goodbye_hex = await goodbye.pool.fetchrow('SELECT bye_hex FROM info WHERE guild_id = $1', guild_id)
        bye_hex = goodbye_hex["bye_hex"]
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

# ============== RAID LOGIC ==============
def is_suspicious_account(member) -> dict:
    """
    Check for suspicious account characteristics.
    Returns dict with boolean flags for suspicious traits.
    """
    flags = {
        'new_account': False,
        'no_avatar': False,
        'bot_like_name': False
    }
    
    # Check if account created less than 7 days ago
    account_age = datetime.now(timezone.utc) - member.created_at
    if account_age < timedelta(days=7):
        flags['new_account'] = True
    
    # Check if account has no avatar
    if member.avatar is None:
        flags['no_avatar'] = True
    
    # Check for bot-like username patterns (numbers at end, excessive numbers)
    username = member.name.lower()
    if re.search(r'\d{3,}', username) or re.search(r'[a-z]+\d+$', username):
        flags['bot_like_name'] = True
    
    return flags

async def check_raid_response_enabled(guild_id, pool) -> bool:
    """Check if raid response is enabled for this guild."""
    try:
        result = await pool.fetchrow(
            'SELECT raid_response_enabled FROM info WHERE guild_id = $1', 
            guild_id
        )
        if result:
            return result['raid_response_enabled']
    except Exception as e:
        logging.error(f"Error checking raid response status: {e}")
    return True  # Default to enabled if not found

def get_suspicious_flags_string(flags: dict) -> str:
    """Convert flags dict to readable string."""
    flag_list = []
    if flags['new_account']:
        flag_list.append("🟠 New Account (< 7 days)")
    if flags['no_avatar']:
        flag_list.append("🟠 No Avatar")
    if flags['bot_like_name']:
        flag_list.append("🟠 Bot-like Username")
    return " | ".join(flag_list) if flag_list else "No red flags"
# ========================================

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
        # ============== RAID LOGIC ==============
        # Check if raid response is enabled
        raid_enabled = await check_raid_response_enabled(member.guild.id, self.pool)
        
        if raid_enabled:
            # Initialize guild tracker if not exists
            if member.guild.id not in raid_join_tracker:
                raid_join_tracker[member.guild.id] = []
            
            # Add current join with timestamp
            current_time_obj = datetime.now(timezone.utc)
            raid_join_tracker[member.guild.id].append({
                'timestamp': current_time_obj,
                'member': member
            })
            
            # Remove joins older than detection window
            cutoff_time = current_time_obj - timedelta(seconds=RAID_DETECTION_WINDOW)
            raid_join_tracker[member.guild.id] = [
                j for j in raid_join_tracker[member.guild.id]
                if j['timestamp'] > cutoff_time
            ]
            
            # Check if raid threshold exceeded
            if len(raid_join_tracker[member.guild.id]) >= RAID_JOIN_THRESHOLD:
                # Trigger raid response (will be handled in Raid.py)
                await self.trigger_raid_alert(member.guild, raid_join_tracker[member.guild.id])
        # ========================================
        
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
    
    # ============== RAID LOGIC ==============
    async def trigger_raid_alert(self, guild, joining_members):
        """
        Trigger raid alert with detected members and flags.
        This calls the actual raid response from Raid.py
        """
        try:
            # Import here to avoid circular imports
            from discord.ext import commands
            raid_cog = self.bot.get_cog('raid')
            
            if raid_cog:
                await raid_cog.execute_raid_response(guild, joining_members)
        except Exception as e:
            logging.error(f"Error triggering raid alert: {e}")
    # ========================================
            
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