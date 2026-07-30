import asyncio
import logging
import discord
from discord.ext import commands
from typing import Optional, Dict, Any, List
import database
from config import settings

logger = logging.getLogger("cegbot")

class ReactionBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix="!", intents=intents)
        self.is_connected = False

    async def on_ready(self):
        self.is_connected = True
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        print(f"[Bot] Logged in as {self.user} | Connected to {len(self.guilds)} guild(s)")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.user and payload.user_id == self.user.id:
            return
        
        panel = await database.get_panel_by_message_id(str(payload.message_id))
        if not panel:
            return
        
        emoji_str = str(payload.emoji)
        emoji_name = payload.emoji.name
        
        matched_role_id = None
        for r in panel.get("roles", []):
            stored = r.get("emoji", "").strip()
            if stored == emoji_str or stored == emoji_name or (payload.emoji.id and str(payload.emoji.id) in stored):
                matched_role_id = r.get("role_id")
                break
        
        if not matched_role_id:
            return
        
        guild = self.get_guild(payload.guild_id)
        if not guild:
            try:
                guild = await self.fetch_guild(payload.guild_id)
            except Exception as e:
                logger.error(f"Failed to fetch guild {payload.guild_id}: {e}")
                return

        role = guild.get_role(int(matched_role_id))
        if not role:
            logger.warning(f"Role ID {matched_role_id} not found in guild {guild.name}")
            return

        member = payload.member
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except Exception as e:
                logger.error(f"Failed to fetch member {payload.user_id}: {e}")
                return

        try:
            await member.add_roles(role, reason="Reaction Role assigned via CEGBot Admin Panel")
            print(f"[Bot] Assigned role '{role.name}' to user '{member.display_name}' ({member.id})")
        except discord.Forbidden:
            logger.error(f"Permission denied: Bot higher role hierarchy required to assign role '{role.name}'")
        except Exception as e:
            logger.error(f"Error adding role: {e}")

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if self.user and payload.user_id == self.user.id:
            return

        panel = await database.get_panel_by_message_id(str(payload.message_id))
        if not panel:
            return

        emoji_str = str(payload.emoji)
        emoji_name = payload.emoji.name

        matched_role_id = None
        for r in panel.get("roles", []):
            stored = r.get("emoji", "").strip()
            if stored == emoji_str or stored == emoji_name or (payload.emoji.id and str(payload.emoji.id) in stored):
                matched_role_id = r.get("role_id")
                break

        if not matched_role_id:
            return

        guild = self.get_guild(payload.guild_id)
        if not guild:
            try:
                guild = await self.fetch_guild(payload.guild_id)
            except Exception as e:
                logger.error(f"Failed to fetch guild {payload.guild_id}: {e}")
                return

        role = guild.get_role(int(matched_role_id))
        if not role:
            return

        try:
            member = await guild.fetch_member(payload.user_id)
        except Exception as e:
            logger.error(f"Failed to fetch member {payload.user_id}: {e}")
            return

        try:
            await member.remove_roles(role, reason="Reaction Role removed via CEGBot Admin Panel")
            print(f"[Bot] Removed role '{role.name}' from user '{member.display_name}' ({member.id})")
        except discord.Forbidden:
            logger.error(f"Permission denied: Bot higher role hierarchy required to remove role '{role.name}'")
        except Exception as e:
            logger.error(f"Error removing role: {e}")

    def build_embed(self, panel: Dict[str, Any]) -> discord.Embed:
        color_hex = panel.get("color", "#5865F2").lstrip("#")
        try:
            color_int = int(color_hex, 16)
        except ValueError:
            color_int = 0x5865F2

        embed = discord.Embed(
            title=panel.get("title", "Reaction Roles"),
            description=panel.get("description", ""),
            color=color_int
        )
        
        if panel.get("thumbnail_url"):
            embed.set_thumbnail(url=panel["thumbnail_url"])
        if panel.get("image_url"):
            embed.set_image(url=panel["image_url"])
        if panel.get("footer_text"):
            embed.set_footer(text=panel["footer_text"])
            
        return embed

    async def deploy_panel(self, panel_id: int) -> Dict[str, Any]:
        panel = await database.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError("Panel not found in database")
        
        channel_id = int(panel["channel_id"])
        channel = self.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception as e:
                raise ValueError(f"Could not find or fetch channel ID {channel_id}: {e}")
        
        embed = self.build_embed(panel)
        
        message = None
        if panel.get("message_id"):
            try:
                message = await channel.fetch_message(int(panel["message_id"]))
                await message.edit(embed=embed)
            except Exception:
                message = None

        if not message:
            message = await channel.send(embed=embed)
            await database.update_panel_message_id(panel_id, str(message.id))

        for role_item in panel.get("roles", []):
            emoji_str = role_item.get("emoji", "").strip()
            if emoji_str:
                try:
                    await message.add_reaction(emoji_str)
                except Exception as e:
                    logger.warning(f"Failed to add reaction emoji '{emoji_str}': {e}")
        
        return {
            "status": "success",
            "message_id": str(message.id),
            "channel_id": str(channel.id)
        }

    async def delete_panel_message(self, panel_id: int):
        panel = await database.get_panel_by_id(panel_id)
        if not panel or not panel.get("message_id"):
            return
        
        try:
            channel = self.get_channel(int(panel["channel_id"]))
            if channel:
                msg = await channel.fetch_message(int(panel["message_id"]))
                await msg.delete()
        except Exception as e:
            logger.warning(f"Failed to delete panel message on Discord: {e}")

bot_instance = ReactionBot()
