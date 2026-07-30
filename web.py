from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import os

from bot import bot_instance
import database
from config import settings

app = FastAPI(title="CEGBot Reaction Role Admin API")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class RoleMapping(BaseModel):
    emoji: str
    role_id: str
    role_name: str

class PanelCreateRequest(BaseModel):
    guild_id: str
    channel_id: str
    title: str
    description: str
    color: str = "#5865F2"
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    footer_text: Optional[str] = None
    roles: List[RoleMapping] = []
    deploy_immediately: bool = True

class PanelUpdateRequest(BaseModel):
    guild_id: str
    channel_id: str
    title: str
    description: str
    color: str = "#5865F2"
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    footer_text: Optional[str] = None
    roles: List[RoleMapping] = []
    re_deploy: bool = True

class TokenUpdate(BaseModel):
    token: str

@app.get("/")
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/status")
async def get_bot_status():
    token_set = bool(settings.DISCORD_TOKEN and len(settings.DISCORD_TOKEN) > 10)
    bot_ready = bot_instance.is_ready() and bot_instance.is_connected
    
    bot_user = str(bot_instance.user) if bot_instance.user else "Not Connected"
    guilds_count = len(bot_instance.guilds) if bot_ready else 0
    ping_ms = round(bot_instance.latency * 1000, 2) if bot_ready else 0
    
    return {
        "status": "online" if bot_ready else ("token_required" if not token_set else "connecting"),
        "bot_user": bot_user,
        "guilds_count": guilds_count,
        "latency_ms": ping_ms,
        "token_configured": token_set
    }

@app.post("/api/config/token")
async def update_token(data: TokenUpdate):
    token = data.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token cannot be empty")
    
    settings.save_env_setting("DISCORD_TOKEN", token)
    return {"status": "success", "message": "Token saved. Restart server to re-login bot if running."}

@app.get("/api/guilds")
async def get_guilds():
    if not bot_instance.is_ready():
        return {"guilds": []}
    
    guilds = []
    for g in bot_instance.guilds:
        guilds.append({
            "id": str(g.id),
            "name": g.name,
            "icon_url": str(g.icon.url) if g.icon else None,
            "member_count": g.member_count
        })
    return {"guilds": guilds}

@app.get("/api/guilds/{guild_id}/channels")
async def get_guild_channels(guild_id: str):
    if not bot_instance.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready or connected to Discord")
    
    try:
        guild = bot_instance.get_guild(int(guild_id))
        if not guild:
            guild = await bot_instance.fetch_guild(int(guild_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Guild not found")

    channels = []
    for ch in guild.text_channels:
        perms = ch.permissions_for(guild.me)
        if perms.send_messages:
            channels.append({
                "id": str(ch.id),
                "name": ch.name,
                "category": ch.category.name if ch.category else "No Category"
            })
            
    return {"channels": channels}

@app.get("/api/guilds/{guild_id}/roles")
async def get_guild_roles(guild_id: str):
    if not bot_instance.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready or connected to Discord")
    
    try:
        guild = bot_instance.get_guild(int(guild_id))
        if not guild:
            guild = await bot_instance.fetch_guild(int(guild_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Guild not found")

    roles = []
    bot_top_role = guild.me.top_role
    for r in guild.roles:
        if r.is_default():
            continue
        roles.append({
            "id": str(r.id),
            "name": r.name,
            "color": f"#{r.color.value:06x}" if r.color.value else "#99AAB5",
            "position": r.position,
            "assignable": r < bot_top_role
        })
        
    roles.sort(key=lambda x: x["position"], reverse=True)
    return {"roles": roles}

@app.get("/api/panels")
async def get_panels():
    panels = await database.get_all_panels()
    return {"panels": panels}

@app.get("/api/panels/{panel_id}")
async def get_panel(panel_id: int):
    panel = await database.get_panel_by_id(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return panel

@app.post("/api/panels")
async def create_panel_endpoint(data: PanelCreateRequest):
    roles_dicts = [r.dict() for r in data.roles]
    panel_id = await database.create_panel(
        guild_id=data.guild_id,
        channel_id=data.channel_id,
        title=data.title,
        description=data.description,
        color=data.color,
        thumbnail_url=data.thumbnail_url,
        image_url=data.image_url,
        footer_text=data.footer_text,
        roles=roles_dicts
    )
    
    deploy_res = None
    if data.deploy_immediately and bot_instance.is_ready():
        try:
            deploy_res = await bot_instance.deploy_panel(panel_id)
        except Exception as e:
            deploy_res = {"status": "error", "message": str(e)}

    return {
        "status": "success",
        "panel_id": panel_id,
        "deployment": deploy_res
    }

@app.put("/api/panels/{panel_id}")
async def update_panel_endpoint(panel_id: int, data: PanelUpdateRequest):
    existing = await database.get_panel_by_id(panel_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")

    roles_dicts = [r.dict() for r in data.roles]
    await database.update_panel(
        panel_id=panel_id,
        guild_id=data.guild_id,
        channel_id=data.channel_id,
        title=data.title,
        description=data.description,
        color=data.color,
        thumbnail_url=data.thumbnail_url,
        image_url=data.image_url,
        footer_text=data.footer_text,
        roles=roles_dicts
    )

    deploy_res = None
    if data.re_deploy and bot_instance.is_ready():
        try:
            deploy_res = await bot_instance.deploy_panel(panel_id)
        except Exception as e:
            deploy_res = {"status": "error", "message": str(e)}

    return {
        "status": "success",
        "panel_id": panel_id,
        "deployment": deploy_res
    }

@app.post("/api/panels/{panel_id}/deploy")
async def deploy_panel_endpoint(panel_id: int):
    if not bot_instance.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not connected to Discord")

    try:
        res = await bot_instance.deploy_panel(panel_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/panels/{panel_id}")
async def delete_panel_endpoint(panel_id: int):
    if bot_instance.is_ready():
        await bot_instance.delete_panel_message(panel_id)
        
    await database.delete_panel(panel_id)
    return {"status": "success", "message": "Panel deleted successfully"}
