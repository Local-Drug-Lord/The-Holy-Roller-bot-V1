import discord
import logging
from discord import app_commands, File
from discord.ext import commands
from discord.ext.commands import has_permissions
from datetime import datetime, timezone, timedelta

logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)

# Time helper
def current_time():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S")

# Get logging channel
async def get_logging_channel(guild_id, pool, bot):
    try:
        row = await pool.fetchrow('SELECT log_id FROM info WHERE guild_id = $1', int(guild_id))
        if not row:
            return False
        log_id = row.get('log_id')
        if not log_id:
            return False
        channel = await bot.fetch_channel(int(log_id))
        return channel
    except Exception as e:
        logging.error(f"get_logging_channel failed: {e}")
        return False

# Get all admin members
async def get_admin_members(guild):
    """Get all members with administrator permission."""
    admins = []
    try:
        async for member in guild.fetch_members():
            if member.guild_permissions.administrator and not member.bot:
                admins.append(member)
    except Exception as e:
        logging.error(f"Error fetching admin members: {e}")
    return admins

class raid(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool = bot.pool

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        logging.info("---|raid       cog loaded!|---  %s", current_time())

    # ============== RAID LOGIC ==============
    # Configuration Commands

    @app_commands.command(name="raid", description="Raid protection settings")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(protection=[
        app_commands.Choice(name="enable", value="enable"),
        app_commands.Choice(name="disable", value="disable"),
        app_commands.Choice(name="info", value="info")
    ])
    async def raid_protection_slash(self, interaction: discord.Interaction, protection: app_commands.Choice[str]):
        """Manage raid protection settings."""
        if protection.value == "enable":
            await self._handle_raid_enable(interaction)
        elif protection.value == "disable":
            await self._handle_raid_disable(interaction)
        elif protection.value == "info":
            await self._handle_raid_info(interaction)

    @commands.command(name="raid", aliases=["Raid"])
    @commands.has_permissions(administrator=True)
    async def raid_protection_prefix(self, ctx: commands.Context, action: str = None):
        """Manage raid protection settings (prefix command)."""
        if not action:
            await ctx.send("Usage: `!raid [enable|disable|info]`")
            return
        
        action = action.lower()
        if action == "enable":
            await self._handle_raid_enable(ctx)
        elif action == "disable":
            await self._handle_raid_disable(ctx)
        elif action == "info":
            await self._handle_raid_info(ctx)
        else:
            await ctx.send(f"Unknown action `{action}`. Use: enable, disable, or info")

    async def _handle_raid_enable(self, interaction_or_ctx):
        """Internal handler: Enable raid response."""
        is_slash = isinstance(interaction_or_ctx, discord.Interaction)
        guild_id = interaction_or_ctx.guild.id if is_slash else interaction_or_ctx.guild.id
        
        try:
            await self.pool.execute(
                'INSERT INTO info (guild_id, raid_response_enabled) VALUES ($1, $2) '
                'ON CONFLICT (guild_id) DO UPDATE SET raid_response_enabled = $2',
                guild_id, True
            )
            msg = "✅ **Raid response enabled** for this server."
            if is_slash:
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            logging.info(f"Raid response enabled for guild {guild_id}")
        except Exception as e:
            msg = "❌ Error enabling raid response."
            if is_slash:
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            logging.error(f"Error enabling raid response: {e}")

    async def _handle_raid_disable(self, interaction_or_ctx):
        """Internal handler: Disable raid response."""
        is_slash = isinstance(interaction_or_ctx, discord.Interaction)
        guild_id = interaction_or_ctx.guild.id if is_slash else interaction_or_ctx.guild.id
        
        try:
            await self.pool.execute(
                'INSERT INTO info (guild_id, raid_response_enabled) VALUES ($1, $2) '
                'ON CONFLICT (guild_id) DO UPDATE SET raid_response_enabled = $2',
                guild_id, False
            )
            msg = "⛔ **Raid response disabled** for this server."
            if is_slash:
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            logging.info(f"Raid response disabled for guild {guild_id}")
        except Exception as e:
            msg = "❌ Error disabling raid response."
            if is_slash:
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            logging.error(f"Error disabling raid response: {e}")

    async def _handle_raid_info(self, interaction_or_ctx):
        """Internal handler: Display raid response info."""
        is_slash = isinstance(interaction_or_ctx, discord.Interaction)
        guild_id = interaction_or_ctx.guild.id if is_slash else interaction_or_ctx.guild.id
        
        try:
            result = await self.pool.fetchrow(
                'SELECT raid_response_enabled FROM info WHERE guild_id = $1',
                guild_id
            )
            
            status = "🟢 Enabled" if (result and result['raid_response_enabled']) else "🔴 Disabled"
            
            embed = discord.Embed(
                title="🚨 Raid Response Settings",
                description=f"**Status:** {status}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Detection Threshold", value="4 joins in 2 seconds", inline=False)
            embed.add_field(name="Alerts", value="Logging channel + Admin DMs + Guild owner", inline=False)
            embed.add_field(name="Lockdown", value="Disables invites and DMs for 1 hour", inline=False)
            embed.add_field(name="Account Checks", value="New account (< 7 days), No avatar, Bot-like username", inline=False)
            embed.set_footer(text=f"UTC: {current_time()}")
            embed.set_thumbnail(url="attachment://raid_icon.png")
            
            # Try to send with icon, fallback if file doesn't exist
            try:
                file = File("Images/moderation_icon.png", filename="raid_icon.png")
                if is_slash:
                    await interaction_or_ctx.response.send_message(file=file, embed=embed, ephemeral=True)
                else:
                    await interaction_or_ctx.send(file=file, embed=embed)
            except:
                if is_slash:
                    await interaction_or_ctx.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction_or_ctx.send(embed=embed)
                
        except Exception as e:
            msg = "❌ Error fetching raid info."
            if is_slash:
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            logging.error(f"Error in raid_info: {e}")

    # Raid Response Execution

    async def execute_raid_response(self, guild, joining_members):
        """
        Execute full raid response:
        1. Send alert to logging channel
        2. Send alerts to admin DMs
        3. Send alert to guild owner
        4. Lock down guild (pause invites and DMs)
        """
        try:
            # Get logging channel
            log_channel = await get_logging_channel(guild.id, self.pool, self.bot)
            
            # Build raid alert embed
            alert_embed = await self._build_raid_alert_embed(guild, joining_members)
            
            # Send to logging channel
            if log_channel:
                try:
                    file = File("Images/moderation_icon.png", filename="moderation_icon.png")
                    await log_channel.send(file=file, embed=alert_embed)
                except:
                    await log_channel.send(embed=alert_embed)
                logging.info(f"Raid alert sent to logging channel for guild {guild.id}")
            
            # Send to all admins via DM (deduplicated)
            admins = await get_admin_members(guild)
            admin_embed = await self._build_raid_alert_embed(guild, joining_members, is_dm=True)
            
            # Track sent users to avoid duplicate DMs
            notified_ids = set()
            
            for admin in admins:
                try:
                    await admin.send(embed=admin_embed)
                    notified_ids.add(admin.id)
                    logging.info(f"Raid alert DM sent to {admin} ({admin.id})")
                except:
                    logging.warning(f"Could not send raid DM to {admin} ({admin.id})")
            
            # Send to guild owner only if not already notified as admin
            if guild.owner.id not in notified_ids:
                try:
                    await guild.owner.send(embed=admin_embed)
                    logging.info(f"Raid alert DM sent to guild owner {guild.owner} ({guild.owner.id})")
                except:
                    logging.warning(f"Could not send raid DM to guild owner {guild.owner} ({guild.owner.id})")
            
            # Execute guild lockdown
            await self._lockdown_guild(guild)
            
        except Exception as e:
            logging.error(f"Error executing raid response: {e}")

    async def _build_raid_alert_embed(self, guild, joining_members, is_dm=False) -> discord.Embed:
        """Build the raid alert embed."""
        # Import here to avoid circular imports
        from cogs.Greetings import is_suspicious_account, get_suspicious_flags_string
        
        embed = discord.Embed(
            title="🚨 RAID ALERT 🚨",
            description=f"**{len(joining_members)} rapid member joins detected in {RAID_DETECTION_WINDOW} seconds**",
            color=discord.Color.red()
        )
        
        # Add detected members
        members_info = []
        for join_data in joining_members:
            member = join_data['member']
            flags = is_suspicious_account(member)
            flag_str = get_suspicious_flags_string(flags)
            
            account_age = datetime.now(timezone.utc) - member.created_at
            age_str = f"{account_age.days}d {account_age.seconds // 3600}h"
            
            members_info.append(
                f"**{member}** ({member.id})\n"
                f"Created: {age_str} ago\n"
                f"Flags: {flag_str}"
            )
        
        # Add members in chunks to avoid embed field limits
        for i, info in enumerate(members_info):
            embed.add_field(name=f"Member {i+1}", value=info, inline=False)
        
        embed.add_field(name="Detection Window", value=f"{RAID_DETECTION_WINDOW} seconds", inline=True)
        embed.add_field(name="Threshold", value="4 joins", inline=True)
        
        if not is_dm:
            embed.add_field(
                name="Actions Taken",
                value="✅ Invites paused\n✅ DMs disabled for 1 hour\n✅ Admins notified",
                inline=False
            )
        
        embed.set_footer(text=f"Raid detected at: {current_time()}")
        embed.set_thumbnail(url="attachment://moderation_icon.png")
        
        return embed

    async def _lockdown_guild(self, guild):
        """Lock down guild by disabling invites and DMs."""
        try:
            lockdown_until = datetime.now(timezone.utc) + timedelta(hours=1)
            
            await guild.edit(
                invites_disabled_until=lockdown_until,
                dms_disabled_until=lockdown_until,
                reason="Raid detected - automatic lockdown"
            )
            logging.info(f"Guild {guild.id} locked down due to raid for 1 hour")
        except discord.Forbidden:
            logging.warning(f"No permission to lock down guild {guild.id}")
        except Exception as e:
            logging.error(f"Error locking down guild {guild.id}: {e}")

    # ========================================

    @raid_protection_slash.error
    async def raid_protection_slash_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission to use this command.",
                ephemeral=True
            )

    @raid_protection_prefix.error
    async def raid_protection_prefix_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need **Administrator** permission to use this command.")


# Constants (must be defined after imports)
RAID_DETECTION_WINDOW = 2  # Seconds


async def setup(bot):
    await bot.add_cog(raid(bot))
