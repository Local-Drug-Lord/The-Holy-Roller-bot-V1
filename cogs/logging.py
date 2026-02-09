import discord
import logging
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import io

# Time

def current_time():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def create_standard_update_embed(title: str, description: str, before_value: str, after_value: str, *, color=None, executor_name: str = None, executor_id: int = None):
    try:
        clr = color if color is not None else discord.Color.orange()
        embed = discord.Embed(title=title, description=description, color=clr, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Before", value=before_value or "None", inline=False)
        embed.add_field(name="After", value=after_value or "None", inline=False)

        # Prepare footer values (show executor when known, otherwise 'N/A')
        name = executor_name if executor_name is not None else "N/A"
        eid = str(executor_id) if executor_id is not None else "N/A"
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"Action made by: {name} ({eid}).  \nUTC: {ts}"
        embed.set_footer(text=footer_text)
        embed.set_thumbnail(url="attachment://moderation_icon.png")
        return embed
    except Exception:
        logging.exception("create_standard_update_embed failed")
        # Fallback minimal embed
        try:
            embed = discord.Embed(title=title, description=description, color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Before", value=before_value or "None", inline=False)
            embed.add_field(name="After", value=after_value or "None", inline=False)
            return embed
        except Exception:
            return None

# Permission labels for prettier display
PERM_LABELS = {
    'view_channel': 'View Channel',
    'send_messages': 'Send Messages',
    'send_tts_messages': 'Send TTS Messages',
    'manage_messages': 'Manage Messages',
    'embed_links': 'Embed Links',
    'attach_files': 'Attach Files',
    'read_message_history': 'Read Message History',
    'mention_everyone': 'Mention everyone',
    'use_external_emojis': 'Use External Emojis',
    'add_reactions': 'Add Reactions',
    'manage_roles': 'Manage Roles',
    'manage_channels': 'Manage Channels',
    'manage_webhooks': 'Manage Webhooks',
    'connect': 'Connect (voice)',
    'speak': 'Speak (voice)',
    'mute_members': 'Mute Members',
    'deafen_members': 'Deafen Members',
    'move_members': 'Move Members',
    'priority_speaker': 'Priority Speaker',
    'create_instant_invite': 'Create Instant Invite',
    'manage_threads': 'Manage Threads',
    'send_messages_in_threads': 'Send Messages In Threads',
    'use_application_commands': 'Use Application Commands',
    'moderate_members': 'Moderate Members'
}

def _pretty_perm_label(key: str) -> str:
    return PERM_LABELS.get(key, key.replace('_', ' ').title())

def _perm_state_symbol(state: str) -> str:
    if state == 'Allow':
        return ':green_square:'
    if state == 'Disallow':
        return ':red_square:'
    return ':white_large_square:'

def _format_perm_state(key: str, state: str) -> str:
    # place the emoji on the right side of permission
    return f"{_pretty_perm_label(key)} {_perm_state_symbol(state)}"

# Get logging channel

async def get_logging_channel(cog, guild_id):
    try:
        row = await cog.pool.fetchrow('SELECT log_id FROM info WHERE guild_id = $1', int(guild_id))
        if not row:
            return False
        log_id = row.get('log_id')
        if not log_id:
            return False
        channel = await cog.bot.fetch_channel(int(log_id))
        return channel
    except Exception:
        logging.exception("get_logging_channel failed")
        return False

# Produce simple before/after lists for attribute diffs used in some update logs

def format_lockdown_status(dt_value):
    if dt_value is None:
        return "Disabled"
    try:
        if isinstance(dt_value, datetime):
            return dt_value.strftime("Enabled until %Y-%m-%d %H:%M UTC")
        else:
            return "Disabled"
    except Exception:
        return "Disabled"

def diff_attrs(before, after, attrs):
    before_lines = []
    after_lines = []
    for a in attrs:
        try:
            b = getattr(before, a, None)
            c = getattr(after, a, None)
            
            # Special formatting for lockdown attributes
            if a in ['invites_disabled_until', 'dms_disabled_until']:
                b_str = format_lockdown_status(b)
                c_str = format_lockdown_status(c)
                # Use friendly names instead of technical attribute names
                display_name = "Invites" if a == 'invites_disabled_until' else "DMs"
            else:
                b_str = str(b) if b is not None else 'None'
                c_str = str(c) if c is not None else 'None'
                display_name = a
            
            if b_str != c_str:
                before_lines.append(f"{display_name}: {b_str}")
                after_lines.append(f"{display_name}: {c_str}")
        except Exception:
            continue
    return before_lines, after_lines

# Minimal role summary

def format_role_summary(role):
    try:
        perms = [p[0] for p in role.permissions if p[1]] if hasattr(role, 'permissions') else []
    except Exception:
        perms = []
    return f"Name: {role.name} | ID: {role.id} | Permissions: {', '.join(perms)[:800]}"


# Format a timeout datetime into a readable string (UTC + duration remaining)
def format_timeout_display(dt):
    try:
        if dt is None:
            return None
        now = datetime.now(timezone.utc)
        if getattr(dt, 'tzinfo', None) is None:
            dt = dt.replace(tzinfo=timezone.utc)
        remaining = dt - now
        # Format remaining as H:MM:SS (timedelta default str is OK)
        rem_str = str(remaining).split('.')[0]
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"{dt_str} ({rem_str})"
    except Exception:
        return str(dt)


# Find who executed an audit-log action for a given target id
async def find_audit_executor(cog, guild, action, target_id, window: int = 30):
    try:
        now = datetime.now(timezone.utc)
        # normalize target id
        try:
            target_val = int(getattr(target_id, 'id', target_id))
        except Exception:
            target_val = getattr(target_id, 'id', None) if hasattr(target_id, 'id') else None
        async for entry in guild.audit_logs(limit=24, action=action):
            try:
                entry_target_id = getattr(entry.target, 'id', None)
                if entry_target_id is None:
                    # some audit entries may store the target differently; compare string repr fallback
                    if str(entry.target) == str(target_id):
                        entry_target_id = getattr(entry.target, 'id', None)
                if entry_target_id is None and target_val is None:
                    continue
                if entry_target_id is not None and target_val is not None and int(entry_target_id) == int(target_val):
                    if (now - entry.created_at).total_seconds() <= window:
                        author = entry.user
                        reason = entry.reason if getattr(entry, 'reason', None) else None
                        return (author, reason)
            except Exception:
                continue
    except discord.Forbidden:
        logging.warning("find_audit_executor: missing View Audit Log permission for guild %s", getattr(guild, 'id', None))
    except Exception:
        logging.exception("find_audit_executor: error while reading audit logs")
    return (None, None)


def _format_overwrite_obj(o):
    try:
        # If it's a PermissionOverwrite, produce per-permission Allow/Disallow/N/A lines
        if isinstance(o, discord.PermissionOverwrite):
            perms = [
                'view_channel', 'send_messages', 'send_tts_messages', 'manage_messages', 'embed_links', 'attach_files',
                'read_message_history', 'mention_everyone', 'use_external_emojis', 'add_reactions', 'manage_roles',
                'manage_channels', 'manage_webhooks', 'connect', 'speak', 'mute_members', 'deafen_members', 'move_members',
                'priority_speaker', 'create_instant_invite', 'manage_threads', 'send_messages_in_threads',
                'use_application_commands', 'moderate_members'
            ]
            parts = []
            try:
                allow, deny = o.pair()
            except Exception:
                allow = None
                deny = None
            for p in perms:
                a = getattr(allow, p, False) if allow is not None else False
                d = getattr(deny, p, False) if deny is not None else False
                # Only include permissions explicitly set (Allow or Disallow). If neither, treat as N/A and skip.
                if a and not d:
                    state = 'Allow'
                elif d and not a:
                    state = 'Disallow'
                else:
                    continue
                parts.append(f"{p}: {state}")
            # return one-per-line, indented for readability
            if parts:
                # map keys to pretty labels with emoji
                pretty_lines = []
                for raw in parts:
                    try:
                        if isinstance(raw, str) and ': ' in raw:
                            k, st = raw.split(': ', 1)
                            pretty_lines.append(_format_perm_state(k, st))
                        else:
                            pretty_lines.append(str(raw))
                    except Exception:
                        pretty_lines.append(str(raw))
                return "\n  " + "\n  ".join(pretty_lines)
            return str(o)
        # Role/User object keys - show a readable name
        try:
            name = getattr(o, 'name', None) or getattr(o, 'display_name', None) or getattr(o, 'mention', None) or str(o)
            return str(name)
        except Exception:
            return str(o)
    except Exception:
        return repr(o)


def diff_overwrites(before, after):
    lines = []
    try:
        before_map = getattr(before, 'overwrites', None) or getattr(before, 'overwrites_map', None) or {}
        after_map = getattr(after, 'overwrites', None) or getattr(after, 'overwrites_map', None) or {}
        # Normalize to dicts
        try:
            before_items = dict(before_map.items())
        except Exception:
            before_items = dict(before_map) if isinstance(before_map, dict) else {}
        try:
            after_items = dict(after_map.items())
        except Exception:
            after_items = dict(after_map) if isinstance(after_map, dict) else {}

        perms = [
            'view_channel', 'send_messages', 'send_tts_messages', 'manage_messages', 'embed_links', 'attach_files',
            'read_message_history', 'mention_everyone', 'use_external_emojis', 'add_reactions', 'manage_roles',
            'manage_channels', 'manage_webhooks', 'connect', 'speak', 'mute_members', 'deafen_members', 'move_members',
            'priority_speaker', 'create_instant_invite', 'manage_threads', 'send_messages_in_threads',
            'use_application_commands', 'moderate_members'
        ]

        all_keys = set(list(before_items.keys()) + list(after_items.keys()))
        for key in all_keys:
            b = before_items.get(key)
            a = after_items.get(key)

            def build_state_map(obj):
                state = {}
                if obj is None:
                    return state
                try:
                    allow, deny = obj.pair()
                except Exception:
                    allow = None
                    deny = None
                for p in perms:
                    a_val = getattr(allow, p, False) if allow is not None else False
                    d_val = getattr(deny, p, False) if deny is not None else False
                    if a_val and not d_val:
                        state[p] = 'Allow'
                    elif d_val and not a_val:
                        state[p] = 'Disallow'
                    else:
                        # N/A, skip
                        continue
                return state

            state_b = build_state_map(b)
            state_a = build_state_map(a)

            if not state_b and state_a:
                # Added overwrite: list only explicitly set perms in 'a'
                block = "\n  ".join([_format_perm_state(p, state_a[p]) for p in perms if p in state_a])
                lines.append(f"Added overwrite for {key}:\n  {block}")
            elif not state_a and state_b:
                # Removed overwrite: list only explicitly set perms in 'b'
                block = "\n  ".join([_format_perm_state(p, state_b[p]) for p in perms if p in state_b])
                lines.append(f"Removed overwrite for {key}:\n  {block}")
            else:
                # Compare per-permission and include only those that changed
                changed_perms = [p for p in perms if state_b.get(p) != state_a.get(p)]
                if changed_perms:
                    before_block = "\n  ".join([_format_perm_state(p, state_b.get(p, 'N/A')) for p in changed_perms])
                    after_block = "\n  ".join([_format_perm_state(p, state_a.get(p, 'N/A')) for p in changed_perms])
                    lines.append(f"Changed overwrite for {key}:\nBefore:\n  {before_block}\nAfter:\n  {after_block}")
    except Exception:
        logging.exception("diff_overwrites failed")
    return lines


def diff_integrations(before, after):
    lines = []
    try:
        before_int = [getattr(i, 'name', str(i)) for i in getattr(before, 'integrations', []) or []]
        after_int = [getattr(i, 'name', str(i)) for i in getattr(after, 'integrations', []) or []]
        added = [i for i in after_int if i not in before_int]
        removed = [i for i in before_int if i not in after_int]
        for a in added:
            lines.append(f"Integration added: {a}")
        for r in removed:
            lines.append(f"Integration removed: {r}")
    except Exception:
        logging.exception("diff_integrations failed")
    return lines

# Logging

class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool = bot.pool
        self._recent_channel_updates = {}

    # Check recent moderation actions from The Holy Roller

    def _pop_recent_action(self, guild_id: int, user_id: int, action: str, window: int = 10):
        try:
            bot_store = getattr(self.bot, 'recent_mod_actions', None)
            if not bot_store:
                return None
            key = (int(guild_id), int(user_id))
            entry = bot_store.get(key)
            if not entry:
                return None
            entry_action = entry[0]
            entry_time = entry[1]
            now = datetime.now(timezone.utc)
            if entry_action == action and (now - entry_time).total_seconds() <= window:
                try:
                    bot_store.pop(key, None)
                except Exception:
                    pass
                return entry
        except Exception:
            logging.exception("_pop_recent_action failed")
        return None

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("---|Logging    cog loaded!|---  %s", current_time())

    # Log message deletions

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None or message.author.bot:
            return
        channel = await get_logging_channel(self, message.guild.id)
        if channel:
            # Build embed
            content = message.content or ""
            embed = discord.Embed(
                title="Message Deleted",
                description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Content:** {content}",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Action made by: {message.author} ({message.author.id}).\nUTC: {current_time()}")

            # If the message had attachments, try to include them (prefer images)
            try:
                attachments = getattr(message, 'attachments', []) or []
                if attachments:
                    # find first image-like attachment
                    img_url = None
                    img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
                    for a in attachments:
                        try:
                            ctype = getattr(a, 'content_type', None) or ''
                        except Exception:
                            ctype = ''
                        name = getattr(a, 'filename', '') or ''
                        if ctype.startswith('image') or name.lower().endswith(img_exts):
                            img_url = getattr(a, 'url', None)
                            break
                    file_image = None
                    if img_url:
                        # Prefer embedding the attachment as a file (works when attachment URLs are restricted)
                        try:
                            data = await a.read()
                            file_image = discord.File(io.BytesIO(data), filename=getattr(a, 'filename', 'attached_image'))
                            embed.set_image(url=f"attachment://{getattr(a, 'filename', 'attached_image')}")
                        except Exception:
                            # fallback to remote URL if read() fails
                            try:
                                embed.set_image(url=img_url)
                            except Exception:
                                pass
                    # list attachments as field for reference
                    try:
                        att_lines = [f"{getattr(a, 'filename', str(a))}: {getattr(a, 'url', '')}" for a in attachments]
                        embed.add_field(name="Attachments", value="\n".join(att_lines)[:1024], inline=False)
                    except Exception:
                        pass
            except Exception:
                logging.exception("on_message_delete: failed to process attachments")

            icon_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            embed.set_thumbnail(url="attachment://moderation_icon.png")
            try:
                if file_image:
                    await channel.send(files=[icon_file, file_image], embed=embed)
                else:
                    await channel.send(file=icon_file, embed=embed)
            except Exception:
                logging.exception("on_message_delete: failed to send embed")

    # Log message edits (before/after)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild is None or before.author.bot or before.content == after.content:
            return
        channel = await get_logging_channel(self, before.guild.id)
        if channel:
            desc = f"The content of a message by {before.author.mention} in {before.channel.mention} was updated."
            embed = create_standard_update_embed("Message Edited", desc, before.content or "None", after.content or "None", color=discord.Color.orange())

            # If either version had attachments, include them. Prefer showing the 'before' image if available.
            try:
                b_atts = getattr(before, 'attachments', []) or []
                a_atts = getattr(after, 'attachments', []) or []
                img_url = None
                img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
                for a in b_atts:
                    try:
                        ctype = getattr(a, 'content_type', None) or ''
                    except Exception:
                        ctype = ''
                    name = getattr(a, 'filename', '') or ''
                    if ctype.startswith('image') or name.lower().endswith(img_exts):
                        img_url = getattr(a, 'url', None)
                        break
                if not img_url:
                    for a in a_atts:
                        try:
                            ctype = getattr(a, 'content_type', None) or ''
                        except Exception:
                            ctype = ''
                        name = getattr(a, 'filename', '') or ''
                        if ctype.startswith('image') or name.lower().endswith(img_exts):
                            img_url = getattr(a, 'url', None)
                            break
                file_image = None
                if img_url:
                    # Prefer embedding the attachment as a file (works when attachment URLs are restricted)
                    try:
                        data = await a.read()
                        file_image = discord.File(io.BytesIO(data), filename=getattr(a, 'filename', 'attached_image'))
                        embed.set_image(url=f"attachment://{getattr(a, 'filename', 'attached_image')}")
                    except Exception:
                        try:
                            embed.set_image(url=img_url)
                        except Exception:
                            pass
                # include attachments lists
                try:
                    if b_atts:
                        b_lines = [f"{getattr(x, 'filename', str(x))}: {getattr(x, 'url', '')}" for x in b_atts]
                        embed.add_field(name="Before Attachments", value="\n".join(b_lines)[:1024], inline=False)
                    if a_atts:
                        a_lines = [f"{getattr(x, 'filename', str(x))}: {getattr(x, 'url', '')}" for x in a_atts]
                        embed.add_field(name="After Attachments", value="\n".join(a_lines)[:1024], inline=False)
                except Exception:
                    pass
            except Exception:
                logging.exception("on_message_edit: failed to process attachments")

            icon_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            try:
                if file_image:
                    await channel.send(files=[icon_file, file_image], embed=embed)
                else:
                    await channel.send(file=icon_file, embed=embed)
            except Exception:
                logging.exception("on_message_edit: failed to send embed")

    # New member joined the guild

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await get_logging_channel(self, member.guild.id)
        if channel:
            embed = discord.Embed(
                title="Member Joined",
                description=f"{member.mention} ({member.id}) joined the server.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Action made by: {member} ({member.id}).\nUTC: {current_time()}")
            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            embed.set_thumbnail(url="attachment://moderation_icon.png")
            try:
                await channel.send(file=image_file, embed=embed)
            except Exception:
                logging.exception("on_member_join: failed to send embed")

    # Member left or was kicked (combined handler)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await get_logging_channel(self, member.guild.id)
        if not channel:
            return
        kicked = False

        # Look for a recent kick in the audit log
        async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                entry_meta = self._pop_recent_action(member.guild.id, member.id, "kicked")
                if entry_meta:
                    try:
                        _, _, author_id, reason, time_val, log_channel_id = entry_meta
                    except Exception:
                        author_id = None
                        reason = None
                        time_val = None
                        log_channel_id = None

                    target_channel = None
                    try:
                        if log_channel_id:
                            target_channel = await self.bot.fetch_channel(int(log_channel_id))
                    except Exception:
                        logging.exception("on_member_remove: failed to fetch stored log channel id for kick")
                        target_channel = None
                    if not target_channel:
                        target_channel = channel

                    try:
                        author_name = await self.bot.fetch_user(int(author_id)) if author_id else None
                    except Exception:
                        author_name = None

                    image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
                    log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
                    if reason is None:
                        log_entry_embed.add_field(name="", value=f"User **{member}** was kicked by **{author_name}**.", inline=True)
                    else:
                        log_entry_embed.add_field(name="", value=f"User **{member}** was kicked by **{author_name}** for **{reason}**.", inline=True)
                    log_entry_embed.add_field(name="", value= f"User ID: **{member.id}**")
                    log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
                    log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
                    try:
                        await target_channel.send(file=image_file, embed=log_entry_embed)
                    except Exception:
                        logging.exception("on_member_remove: failed to send moderation embed for kick")
                    kicked = True
                    break

                try:
                    author_name = entry.user if entry.user else None
                    author_id = entry.user.id if entry.user else None
                except Exception:
                    author_name = None
                    author_id = None
                reason = entry.reason if getattr(entry, 'reason', None) else None

                image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
                log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
                if reason is None:
                    log_entry_embed.add_field(name="", value=f"User **{member}** was kicked by **{author_name}**.", inline=True)
                else:
                    log_entry_embed.add_field(name="", value=f"User **{member}** was kicked by **{author_name}** for **{reason}**.", inline=True)
                log_entry_embed.add_field(name="", value= f"User ID: **{member.id}**")
                log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
                log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
                try:
                    await channel.send(file=image_file, embed=log_entry_embed)
                except Exception:
                    logging.exception("on_member_remove: failed to send moderation embed for kick (audit)")
                kicked = True
                break

        if not kicked:
            embed = discord.Embed(
                title="Member Left",
                description=f"{member.mention} ({member.id}) left the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Action made by: {member} ({member.id}).\nUTC: {current_time()}")
            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            embed.set_thumbnail(url="attachment://moderation_icon.png")
            try:
                await channel.send(file=image_file, embed=embed)
            except Exception:
                logging.exception("on_member_remove: failed to send Member Left embed")

    # Log bans (uses audit log or stored metadata)
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = await get_logging_channel(self, guild.id)
        if not channel:
            return

        entry = self._pop_recent_action(guild.id, user.id, "banned")
        if entry:
            try:
                _, _, author_id, reason, time_val, log_channel_id = entry
            except Exception:
                author_id = None
                reason = None
                time_val = None
                log_channel_id = None

            target_channel = None
            try:
                if log_channel_id:
                    target_channel = await self.bot.fetch_channel(int(log_channel_id))
            except Exception:
                logging.exception("on_member_ban: failed to fetch stored log channel id")
                target_channel = None

            if not target_channel:
                target_channel = channel

            try:
                author_name = await self.bot.fetch_user(int(author_id)) if author_id else None
            except Exception:
                author_name = None

            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
            log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
            if reason is None:
                log_entry_embed.add_field(name="", value=f"User **{user}** was banned by **{author_name}**.", inline=True)
            else:
                log_entry_embed.add_field(name="", value=f"User **{user}** was banned by **{author_name}** for **{reason}**.", inline=True)
            log_entry_embed.add_field(name="", value= f"User ID: **{user.id}**")
            log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png") 
            log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
            try:
                await target_channel.send(file=image_file, embed=log_entry_embed)
            except Exception:
                logging.exception("on_member_ban: failed to send moderation embed")
            return

        moderator = None
        mod_reason = None
        try:
            async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.ban):
                if entry.target and getattr(entry.target, 'id', None) == getattr(user, 'id', None) and (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 20:
                    moderator = entry.user
                    mod_reason = entry.reason
                    break
        except discord.Forbidden:
            logging.warning("on_member_ban: missing permissions to read audit logs for guild %s", guild.id)
        except Exception:
            logging.exception("on_member_ban: error while reading audit logs")

        if mod_reason is None:
            try:
                ban_entry = await guild.fetch_ban(user)
                if ban_entry and getattr(ban_entry, 'reason', None):
                    mod_reason = ban_entry.reason
            except discord.NotFound:
                pass
            except discord.Forbidden:
                logging.warning("on_member_ban: missing permission to fetch ban info for guild %s", guild.id)
            except Exception:
                logging.exception("on_member_ban: error while fetching ban info")

        try:
            author_name = moderator if moderator else None
            author_id = moderator.id if moderator else None
        except Exception:
            author_name = None
            author_id = None

        image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
        log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
        if mod_reason is None:
            log_entry_embed.add_field(name="", value=f"User **{user}** was banned by **{author_name}**.", inline=True)
        else:
            log_entry_embed.add_field(name="", value=f"User **{user}** was banned by **{author_name}** for **{mod_reason}**.", inline=True)
        log_entry_embed.add_field(name="", value= f"User ID: **{user.id}**")
        log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
        log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
        try:
            await channel.send(file=image_file, embed=log_entry_embed)
        except Exception:
            logging.exception("on_member_ban: failed to send moderation embed (fallback)")

    # Log unbans (uses audit log or stored metadata)
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = await get_logging_channel(self, guild.id)
        if not channel:
            return

        entry_meta = self._pop_recent_action(guild.id, user.id, "unbanned")
        if entry_meta:
            try:
                _, _, author_id, reason, time_val, log_channel_id = entry_meta
            except Exception:
                author_id = None
                reason = None
                time_val = None
                log_channel_id = None

            target_channel = None
            try:
                if log_channel_id:
                    target_channel = await self.bot.fetch_channel(int(log_channel_id))
            except Exception:
                logging.exception("on_member_unban: failed to fetch stored log channel id")
                target_channel = None
            if not target_channel:
                target_channel = channel

            try:
                author_name = await self.bot.fetch_user(int(author_id)) if author_id else None
            except Exception:
                author_name = None

            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
            log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
            if reason is None:
                log_entry_embed.add_field(name="", value=f"User **{user}** was unbanned by **{author_name}**.", inline=True)
            else:
                log_entry_embed.add_field(name="", value=f"User **{user}** was unbanned by **{author_name}** for **{reason}**.", inline=True)
            log_entry_embed.add_field(name="", value= f"User ID: **{user.id}**")
            log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
            log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
            try:
                await target_channel.send(file=image_file, embed=log_entry_embed)
            except Exception:
                logging.exception("on_member_unban: failed to send moderation embed")
            return

        moderator = None
        mod_reason = None
        try:
            async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.unban):
                if entry.target and getattr(entry.target, 'id', None) == getattr(user, 'id', None) and (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 20:
                    moderator = entry.user
                    mod_reason = entry.reason
                    break
        except discord.Forbidden:
            logging.warning("on_member_unban: missing permissions to read audit logs for guild %s", guild.id)
        except Exception:
            logging.exception("on_member_unban: error while reading audit logs")

        try:
            author_name = moderator if moderator else None
            author_id = moderator.id if moderator else None
        except Exception:
            author_name = None
            author_id = None

        image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
        log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
        if mod_reason is None:
            log_entry_embed.add_field(name="", value=f"User **{user}** was unbanned by **{author_name}**.", inline=True)
        else:
            log_entry_embed.add_field(name="", value=f"User **{user}** was unbanned by **{author_name}** for **{mod_reason}**.", inline=True)
        log_entry_embed.add_field(name="", value= f"User ID: **{user.id}**")
        log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
        log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
        try:
            await channel.send(file=image_file, embed=log_entry_embed)
        except Exception:
            logging.exception("on_member_unban: failed to send moderation embed (fallback)")

    # Log timeouts (mute/unmute) and role changes

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = await get_logging_channel(self, after.guild.id)
        if channel:
            if before.timed_out_until != after.timed_out_until:
                if after.timed_out_until:
                    entry_meta = self._pop_recent_action(after.guild.id, after.id, "muted")
                    if entry_meta:
                        try:
                            _, _, author_id, reason, time_val, log_channel_id = entry_meta
                        except Exception:
                            author_id = None
                            reason = None
                            time_val = None
                            log_channel_id = None

                        target_channel = None
                        try:
                            if log_channel_id:
                                target_channel = await self.bot.fetch_channel(int(log_channel_id))
                        except Exception:
                            logging.exception("on_member_update: failed to fetch stored log channel id for mute")
                            target_channel = None
                        if not target_channel:
                            target_channel = channel

                        try:
                            author_name = await self.bot.fetch_user(int(author_id)) if author_id else None
                        except Exception:
                            author_name = None

                        image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
                        log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
                        if reason is None:
                            log_entry_embed.add_field(name="", value=f"User **{after}** was muted by **{author_name}**.", inline=True)
                        else:
                            log_entry_embed.add_field(name="", value=f"User **{after}** was muted by **{author_name}** for **{reason}**.", inline=True)
                        if time_val:
                            try:
                                # if time_val is a timedelta (registered by moderation cog), compute expire datetime
                                if isinstance(time_val, timedelta):
                                    expire_dt = datetime.now(timezone.utc) + time_val
                                    time_display = format_timeout_display(expire_dt)
                                else:
                                    # otherwise, try to format as datetime
                                    try:
                                        time_display = format_timeout_display(time_val)
                                    except Exception:
                                        time_display = str(time_val)
                            except Exception:
                                time_display = str(time_val)
                            log_entry_embed.add_field(name="", value=f"Time: **{time_display}**", inline=False)
                        log_entry_embed.add_field(name="", value= f"User ID: **{after.id}**")
                        log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
                        log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
                        try:
                            await target_channel.send(file=image_file, embed=log_entry_embed)
                        except Exception:
                            logging.exception("on_member_update: failed to send moderation embed for mute")
                        return

                else:
                    entry_meta = self._pop_recent_action(after.guild.id, after.id, "unmuted")
                    if entry_meta:
                        try:
                            _, _, author_id, reason, time_val, log_channel_id = entry_meta
                        except Exception:
                            author_id = None
                            reason = None
                            time_val = None
                            log_channel_id = None

                        target_channel = None
                        try:
                            if log_channel_id:
                                target_channel = await self.bot.fetch_channel(int(log_channel_id))
                        except Exception:
                            logging.exception("on_member_update: failed to fetch stored log channel id for unmute")
                            target_channel = None
                        if not target_channel:
                            target_channel = channel

                        try:
                            author_name = await self.bot.fetch_user(int(author_id)) if author_id else None
                        except Exception:
                            author_name = None

                        image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
                        log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
                        if reason is None:
                            log_entry_embed.add_field(name="", value=f"User **{after}** was unmuted by **{author_name}**.", inline=True)
                        else:
                            log_entry_embed.add_field(name="", value=f"User **{after}** was unmuted by **{author_name}** for **{reason}**.", inline=True)
                        log_entry_embed.add_field(name="", value= f"User ID: **{after.id}**")
                        log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
                        log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
                        try:
                            await target_channel.send(file=image_file, embed=log_entry_embed)
                        except Exception:
                            logging.exception("on_member_update: failed to send moderation embed for unmute")
                        return

                moderator = None
                mod_reason = None
                try:
                    now = datetime.now(timezone.utc)
                    async for entry in after.guild.audit_logs(limit=12, action=discord.AuditLogAction.member_update):
                        if entry.target and getattr(entry.target, 'id', None) == getattr(after, 'id', None):
                            if (now - entry.created_at).total_seconds() <= 30:
                                changes = getattr(entry, 'changes', None)
                                found = False
                                if changes:
                                    try:
                                        for ch in changes:
                                            key = getattr(ch, 'key', None)
                                            if key in ('communication_disabled_until', 'timed_out_until'):
                                                found = True
                                                break
                                    except Exception:
                                        if 'communication_disabled_until' in str(changes) or 'timed_out_until' in str(changes):
                                            found = True
                                if found:
                                    moderator = entry.user
                                    mod_reason = getattr(entry, 'reason', None)
                                    break
                except discord.Forbidden:
                    logging.warning("on_member_update: missing View Audit Log permission for guild %s", after.guild.id)
                except Exception:
                    logging.exception("on_member_update: error while reading audit logs for timeout")

                try:
                    author_name = moderator if moderator else None
                    author_id = moderator.id if moderator else None
                except Exception:
                    author_name = None
                    author_id = None

                image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
                log_entry_embed = discord.Embed(title="Moderation action!", color=discord.Color.from_rgb(140,27,27))
                if after.timed_out_until:
                    if mod_reason is None:
                        log_entry_embed.add_field(name="", value=f"User **{after}** was muted by **{author_name}**.", inline=True)
                    else:
                        log_entry_embed.add_field(name="", value=f"User **{after}** was muted by **{author_name}** for **{mod_reason}**.", inline=True)
                    # format timeout into nicer UTC + remaining duration instead of raw datetime
                    try:
                        time_display = format_timeout_display(after.timed_out_until)
                    except Exception:
                        time_display = str(after.timed_out_until)
                    log_entry_embed.add_field(name="", value=f"Time: **{time_display}**", inline=False)
                else:
                    if mod_reason is None:
                        log_entry_embed.add_field(name="", value=f"User **{after}** was unmuted by **{author_name}**.", inline=True)
                    else:
                        log_entry_embed.add_field(name="", value=f"User **{after}** was unmuted by **{author_name}** for **{mod_reason}**.", inline=True)
                log_entry_embed.add_field(name="", value= f"User ID: **{after.id}**")
                log_entry_embed.set_thumbnail(url="attachment://moderation_icon.png")
                log_entry_embed.set_footer(text=f"Action made by: {author_name} ({author_id}).\nUTC: {current_time()}")
                try:
                    await channel.send(file=image_file, embed=log_entry_embed)
                except Exception:
                    logging.exception("on_member_update: failed to send moderation embed for mute/unmute (fallback)")

            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            if added_roles:
                embed = discord.Embed(
                    title="Role Assigned",
                    description=f"{after.mention} ({after.id}) was given role(s): {', '.join([role.mention for role in added_roles])}",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Action made by: {after} ({after.id}).\nUTC: {current_time()}")
                image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
                embed.set_thumbnail(url="attachment://moderation_icon.png")
                try:
                    await channel.send(file=image_file, embed=embed)
                except Exception:
                    logging.exception("on_member_update: failed to send Role Assigned embed")
            if removed_roles:
                embed = discord.Embed(
                    title="Role Removed",
                    description=f"{after.mention} ({after.id}) lost role(s): {', '.join([role.mention for role in removed_roles])}",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Action made by: {after} ({after.id}).\nUTC: {current_time()}")
                image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
                embed.set_thumbnail(url="attachment://moderation_icon.png")
                try:
                    await channel.send(file=image_file, embed=embed)
                except Exception:
                    logging.exception("on_member_update: failed to send Role Removed embed")

    # New invite created

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        channel = await get_logging_channel(self, invite.guild.id)
        if channel:
            embed = discord.Embed(
                title="New Invite Created",
                description=f"Invite `{invite.code}` created by {invite.inviter.mention if invite.inviter else 'Unknown'}.\nChannel: {invite.channel.mention}\nMax Uses: {invite.max_uses or 'Unlimited'}\nExpires: {invite.max_age or 'Never'}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            try:
                inviter_name = invite.inviter
                inviter_id = invite.inviter.id if invite.inviter else None
            except Exception:
                inviter_name = None
                inviter_id = None
            embed.set_footer(text=f"Action made by: {inviter_name} ({inviter_id}).\nUTC: {current_time()}")
            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            embed.set_thumbnail(url="attachment://moderation_icon.png")
            try:
                await channel.send(file=image_file, embed=embed)
            except Exception:
                logging.exception("on_invite_create: failed to send embed")

    # Channel created

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = await get_logging_channel(self, channel.guild.id)
        if log_channel:
            embed = discord.Embed(
                title="Channel Created",
                description=f"Channel {channel.mention} was created.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            # try to find who created the channel via audit log
            try:
                executor, reason = await find_audit_executor(self, channel.guild, discord.AuditLogAction.channel_create, channel, window=30)
            except Exception:
                executor, reason = (None, None)
            if executor:
                embed.set_footer(text=f"Action made by: {executor} ({executor.id}).\nUTC: {current_time()}")
            else:
                embed.set_footer(text=f"Action made by: Unknown.\nUTC: {current_time()}")
            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            embed.set_thumbnail(url="attachment://moderation_icon.png")
            # include initial permission overwrites if present
            try:
                ow_lines = []
                try:
                    ow_map = dict(getattr(channel, 'overwrites', {}) or {})
                except Exception:
                    ow_map = {}
                for k, v in ow_map.items():
                    ow_lines.append(f"{k}: {_format_overwrite_obj(v)}")
                if ow_lines:
                    embed.add_field(name="Permissions", value="\n".join(ow_lines)[:1024], inline=False)
            except Exception:
                logging.exception("on_guild_channel_create: failed to enumerate overwrites")
            try:
                await log_channel.send(file=image_file, embed=embed)
            except Exception:
                logging.exception("on_guild_channel_create: failed to send embed")

    # Channel deleted
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = await get_logging_channel(self, channel.guild.id)
        if log_channel:
            embed = discord.Embed(
                title="Channel Deleted",
                description=f"Channel `{channel.name}` was deleted.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            try:
                executor, reason = await find_audit_executor(self, channel.guild, discord.AuditLogAction.channel_delete, channel, window=30)
            except Exception:
                executor, reason = (None, None)
            if executor:
                embed.set_footer(text=f"Action made by: {executor} ({executor.id}).\nUTC: {current_time()}")
            else:
                embed.set_footer(text=f"Action made by: Unknown.\nUTC: {current_time()}")
            image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
            embed.set_thumbnail(url="attachment://moderation_icon.png")
            try:
                await log_channel.send(file=image_file, embed=embed)
            except Exception:
                logging.exception("on_guild_channel_delete: failed to send embed")

    # Channel updated (show attribute diffs)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        log_channel = await get_logging_channel(self, after.guild.id)
        if not log_channel:
            return

        attrs = ["name", "topic", "nsfw", "position", "category", "bitrate", "user_limit", "rate_limit_per_user", "slowmode_delay", "rtc_region"]
        name_changed = getattr(before, 'name', None) != getattr(after, 'name', None)
        other_attrs = [a for a in attrs if a != 'name']
        before_other, after_other = diff_attrs(before, after, other_attrs)

        desc_target = getattr(before, 'mention', None) or getattr(before, 'name', None) or str(before)

        # suppress near-duplicate channel update events (occurs when discord emits multiple events)
        try:
            now_dt = datetime.now(timezone.utc)
            key_recent = (after.guild.id, after.id)
            last = self._recent_channel_updates.get(key_recent)
            self._recent_channel_updates[key_recent] = now_dt
        except Exception:
            pass
        # build compact Before/After blocks for the standard embed
        try:
            before_parts = []
            after_parts = []
            if name_changed:
                before_parts.append(f"Name: {getattr(before, 'name', 'None')}")
                after_parts.append(f"Name: {getattr(after, 'name', 'None')}")
            if before_other:
                before_parts.append("\n".join(before_other))
            if after_other:
                after_parts.append("\n".join(after_other))
            before_block = "\n".join(before_parts) or "None"
            after_block = "\n".join(after_parts) or "None"
            embed = create_standard_update_embed("Channel Updated", f"The channel {desc_target} was updated.", before_block, after_block, color=discord.Color.orange())
        except Exception:
            logging.exception("on_guild_channel_update: failed to build standard embed, falling back")
            embed = discord.Embed(
                title="Channel Updated",
                description=f"Channel {desc_target} was updated.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            if name_changed:
                embed.add_field(name="Before", value=str(getattr(before, 'name', 'None')) or "None", inline=False)
                embed.add_field(name="After", value=str(getattr(after, 'name', 'None')) or "None", inline=False)
            if before_other or after_other:
                before_block = "\n".join(before_other) or "None"
                after_block = "\n".join(after_other) or "None"
                embed.add_field(name="Details", value=f"Before:\n{before_block}\nAfter:\n{after_block}", inline=False)

        # compute permission diffs per role/user
        perm_map = {}
        try:
            before_map = getattr(before, 'overwrites', None) or getattr(before, 'overwrites_map', None) or {}
            after_map = getattr(after, 'overwrites', None) or getattr(after, 'overwrites_map', None) or {}
            try:
                before_items = dict(before_map.items())
            except Exception:
                before_items = dict(before_map) if isinstance(before_map, dict) else {}
            try:
                after_items = dict(after_map.items())
            except Exception:
                after_items = dict(after_map) if isinstance(after_map, dict) else {}

            perms = [
                'view_channel', 'send_messages', 'send_tts_messages', 'manage_messages', 'embed_links', 'attach_files',
                'read_message_history', 'mention_everyone', 'use_external_emojis', 'add_reactions', 'manage_roles',
                'manage_channels', 'manage_webhooks', 'connect', 'speak', 'mute_members', 'deafen_members', 'move_members',
                'priority_speaker', 'create_instant_invite', 'manage_threads', 'send_messages_in_threads',
                'use_application_commands', 'moderate_members'
            ]

            all_keys = list(set(list(before_items.keys()) + list(after_items.keys())))
            for key in all_keys:
                b = before_items.get(key)
                a = after_items.get(key)

                def build_state_map(obj):
                    state = {}
                    if obj is None:
                        return state
                    try:
                        allow, deny = obj.pair()
                    except Exception:
                        allow = None
                        deny = None
                    for p in perms:
                        a_val = getattr(allow, p, False) if allow is not None else False
                        d_val = getattr(deny, p, False) if deny is not None else False
                        if a_val and not d_val:
                            state[p] = 'Allow'
                        elif d_val and not a_val:
                            state[p] = 'Disallow'
                        else:
                            continue
                    return state

                state_b = build_state_map(b)
                state_a = build_state_map(a)

                if not state_b and state_a:
                    kind = 'Added'
                    lines = [_format_perm_state(p, state_a[p]) for p in perms if p in state_a]
                    text = "\n".join(lines)
                elif not state_a and state_b:
                    kind = 'Removed'
                    lines = [_format_perm_state(p, state_b[p]) for p in perms if p in state_b]
                    text = "\n".join(lines)
                else:
                    changed_perms = [p for p in perms if state_b.get(p) != state_a.get(p)]
                    if not changed_perms:
                        continue
                    kind = 'Changed'
                    before_block = "\n".join([_format_perm_state(p, state_b.get(p, 'N/A')) for p in changed_perms])
                    after_block = "\n".join([_format_perm_state(p, state_a.get(p, 'N/A')) for p in changed_perms])
                    text = f"Before:\n{before_block}\nAfter:\n{after_block}"

                # try to resolve canonical object for mentions (role/member)
                canonical = key
                key_id_val = None
                try:
                    key_id_val = getattr(key, 'id', None)
                except Exception:
                    key_id_val = None
                if key_id_val is None:
                    try:
                        key_id_val = int(key)
                    except Exception:
                        key_id_val = None
                if key_id_val is not None:
                    try:
                        role_obj = after.guild.get_role(key_id_val)
                    except Exception:
                        role_obj = None
                    if role_obj:
                        canonical = role_obj
                    else:
                        try:
                            member_obj = after.guild.get_member(key_id_val)
                        except Exception:
                            member_obj = None
                        if member_obj:
                            canonical = member_obj

                try:
                    if hasattr(canonical, 'mention'):
                        name = getattr(canonical, 'name', None) or getattr(canonical, 'display_name', None) or str(canonical)
                        key_display = f"{canonical.mention} ({name})"
                        key_id = str(getattr(canonical, 'id', key))
                    else:
                        key_display = str(canonical)
                        key_id = str(canonical)
                except Exception:
                    key_display = str(canonical)
                    key_id = str(canonical)

                if key_id not in perm_map:
                    perm_map[key_id] = (canonical, key_display, kind, text)
        except Exception:
            logging.exception("on_guild_channel_update: diff_overwrites failed")

        try:
            int_lines = diff_integrations(before, after)
            if int_lines:
                embed.add_field(name="Integrations", value="\n".join(int_lines)[:1024], inline=False)
        except Exception:
            logging.exception("on_guild_channel_update: diff_integrations failed")

        try:
            executor, reason = await find_audit_executor(self, after.guild, discord.AuditLogAction.channel_update, after, window=60)
        except Exception:
            executor, reason = (None, None)
        try:
            if executor:
                try:
                    exec_name = str(executor)
                except Exception:
                    exec_name = getattr(executor, 'name', 'N/A') or 'N/A'
                exec_id = getattr(executor, 'id', 'N/A') or 'N/A'
            else:
                exec_name = 'N/A'
                exec_id = 'N/A'
        except Exception:
            exec_name = 'N/A'
            exec_id = 'N/A'
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"Action made by: {exec_name} ({exec_id}).  \nUTC: {ts}")

        # decide whether to send the main embed or only per-role permission embeds
        try:
            int_lines = diff_integrations(before, after)
            if int_lines:
                embed.add_field(name="Integrations", value="\n".join(int_lines)[:1024], inline=False)
        except Exception:
            logging.exception("on_guild_channel_update: diff_integrations failed")

        # If the only changes are permission overwrites, skip the main embed and send only per-role messages
        only_perms = bool(perm_map) and not name_changed and not (before_other or after_other) and not int_lines

        if not only_perms:
            # send main embed
            try:
                image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
                embed.set_thumbnail(url="attachment://moderation_icon.png")
                try:
                    await log_channel.send(file=image_file, embed=embed)
                except Exception:
                    logging.exception("on_guild_channel_update: failed to send embed (main)")
            except Exception:
                logging.exception("on_guild_channel_update: preparing main embed failed")

        # send one message per changed overwrite
        try:
            if perm_map:
                for key_id, val in perm_map.items():
                    try:
                        canonical_obj, key_display, kind, text = val
                    except Exception:
                        try:
                            key_display, kind, text = val
                            canonical_obj = None
                        except Exception:
                            canonical_obj = None
                            key_display = str(val)
                            kind = ''
                            text = ''
                    try:
                        perm_embed = discord.Embed(
                            title="Channel Updated",
                            description=f"Channel {before.mention} was updated.",
                            color=discord.Color.orange(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        try:
                            # prefer mention when available, but avoid mentioning the @everyone role
                            if canonical_obj is not None:
                                obj_type = type(canonical_obj).__name__
                                if obj_type == 'Role':
                                    # do not mention @everyone (its id equals the guild id)
                                    try:
                                        if getattr(canonical_obj, 'id', None) == getattr(after.guild, 'id', None):
                                            mention_part = getattr(canonical_obj, 'name', str(key_display))
                                        else:
                                            mention_part = canonical_obj.mention
                                    except Exception:
                                        mention_part = getattr(canonical_obj, 'name', str(key_display))
                                elif obj_type == 'Member':
                                    mention_part = canonical_obj.mention
                                else:
                                    mention_part = str(key_display)
                            else:
                                mention_part = str(key_display).split(' ', 1)[0]
                        except Exception:
                            mention_part = str(key_display)
                        field_value = f"{mention_part} — {kind}\n{text}"
                        perm_embed.add_field(name="Permissions changed", value=field_value[:1024], inline=False)
                        try:
                            try:
                                perm_embed.set_thumbnail(url="attachment://moderation_icon.png")
                            except Exception:
                                pass
                            try:
                                ts_perm = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                                perm_embed.set_footer(text=f"Action made by: {exec_name} ({exec_id}).  \nUTC: {ts_perm}")
                            except Exception:
                                pass
                            file_for_perm = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")
                            await log_channel.send(file=file_for_perm, embed=perm_embed)
                        except Exception:
                            logging.exception("on_guild_channel_update: failed to send perm entry embed for %s", key_display)
                    except Exception:
                        logging.exception("on_guild_channel_update: building perm entry failed for %s", key_display)
        except Exception:
            logging.exception("on_guild_channel_update: sending perm entries failed")

    # Role created (include summary)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        log_channel = await get_logging_channel(self, role.guild.id)
        if not log_channel:
            return
        embed = discord.Embed(
            title="Role Created",
            description=f"Role `{role.name}` ({role.id}) was created.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Role Summary", value=format_role_summary(role), inline=False)
        embed.set_footer(text=f"Action made by: Unknown.\nUTC: {current_time()}")
        image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
        embed.set_thumbnail(url="attachment://moderation_icon.png")
        try:
            await log_channel.send(file=image_file, embed=embed)
        except Exception:
            logging.exception("on_guild_role_create: failed to send embed")

    # Server settings updated

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        log_channel = await get_logging_channel(self, after.id)
        if not log_channel:
            return
        
        # Capture standard guild attribute changes
        attrs = ["name", "region", "icon", "verification_level", "default_notifications", "afk_channel"]
        before_lines, after_lines = diff_attrs(before, after, attrs)
        
        # Get lockdown pause status from the Guild properties (exposed from _incidents_data)
        # Properties: invites_paused_until and dms_paused_until (datetime or None)
        try:
            inv_before = getattr(before, 'invites_paused_until', None)
        except Exception:
            inv_before = None
        
        try:
            inv_after = getattr(after, 'invites_paused_until', None)
        except Exception:
            inv_after = None
        
        try:
            dms_before = getattr(before, 'dms_paused_until', None)
        except Exception:
            dms_before = None
        
        try:
            dms_after = getattr(after, 'dms_paused_until', None)
        except Exception:
            dms_after = None
        
        # Log raw values for debugging
        logging.info("on_guild_update (guild %s): inv_before=%s inv_after=%s dms_before=%s dms_after=%s", 
                    after.id, inv_before, inv_after, dms_before, dms_after)
        
        # Format lockdown statuses
        inv_before_str = format_lockdown_status(inv_before)
        inv_after_str = format_lockdown_status(inv_after)
        dms_before_str = format_lockdown_status(dms_before)
        dms_after_str = format_lockdown_status(dms_after)
        
        # Always add these lines (even if not changed, for clarity on raid events)
        before_lines.append(f"Paused invites: {inv_before_str}")
        after_lines.append(f"Paused invites: {inv_after_str}")
        before_lines.append(f"Paused DMs: {dms_before_str}")
        after_lines.append(f"Paused DMs: {dms_after_str}")
        
        desc = f"The settings of server `{before.name}` ({before.id}) were updated."
        
        # Determine who made the change
        executor_name = None
        executor_id = None
        
        # If invites/DMs pause was activated by bot, attribute to raid protection
        if (inv_after is not None and not inv_before) or (dms_after is not None and not dms_before):
            executor_name = "Holy raid protection"
            executor_id = self.bot.user.id if self.bot.user else "BOT"
        else:
            # Otherwise, try to find the user who made the change via audit log
            try:
                executor, reason = await find_audit_executor(self, after, discord.AuditLogAction.guild_update, after, window=60)
                if executor:
                    executor_name = str(executor)
                    executor_id = executor.id
            except Exception:
                logging.debug("on_guild_update: failed to find audit executor")
        
        try:
            embed = create_standard_update_embed(
                "Server Settings Updated",
                desc,
                "\n".join(before_lines) or "None",
                "\n".join(after_lines) or "None",
                color=discord.Color.orange(),
                executor_name=executor_name,
                executor_id=executor_id
            )
        except Exception:
            logging.exception("on_guild_update: failed to build standard embed, falling back")
            embed = discord.Embed(
                title="Server Settings Updated",
                description=f"Server `{before.name}` ({before.id}) was updated.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Before", value="\n".join(before_lines) or "None", inline=False)
            embed.add_field(name="After", value="\n".join(after_lines) or "None", inline=False)
            # Use executor info if available, otherwise Unknown
            exec_name = executor_name or "Unknown"
            exec_id = executor_id or "N/A"
            embed.set_footer(text=f"Action made by: {exec_name} ({exec_id}).\nUTC: {current_time()}")
        
        image_file = discord.File("Images/moderation_icon.png", filename="moderation_icon.png")  
        embed.set_thumbnail(url="attachment://moderation_icon.png")
        try:
            await log_channel.send(file=image_file, embed=embed)
        except Exception:
            logging.exception("on_guild_update: failed to send embed")

async def setup(bot):
    await bot.add_cog(Logging(bot))