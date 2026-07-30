import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings, BASE_DIR

DATA_FILE = BASE_DIR / "panels.json"
_lock = asyncio.Lock()

def _load_data() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        initial_data = {"next_id": 1, "panels": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        return initial_data
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"next_id": 1, "panels": []}

def _save_data(data: Dict[str, Any]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def init_db():
    async with _lock:
        _load_data()

async def create_panel(
    guild_id: str,
    channel_id: str,
    title: str,
    description: str,
    color: str = "#5865F2",
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
    footer_text: Optional[str] = None,
    roles: List[Dict[str, str]] = None
) -> int:
    async with _lock:
        data = _load_data()
        panel_id = data.get("next_id", 1)
        data["next_id"] = panel_id + 1
        
        new_panel = {
            "id": panel_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "message_id": None,
            "title": title,
            "description": description,
            "color": color or "#5865F2",
            "thumbnail_url": thumbnail_url or "",
            "image_url": image_url or "",
            "footer_text": footer_text or "",
            "roles": roles or [],
            "created_at": datetime.now().isoformat()
        }
        
        data["panels"].append(new_panel)
        _save_data(data)
        return panel_id

async def update_panel_message_id(panel_id: int, message_id: str):
    async with _lock:
        data = _load_data()
        for panel in data["panels"]:
            if panel["id"] == panel_id:
                panel["message_id"] = str(message_id)
                break
        _save_data(data)

async def update_panel(
    panel_id: int,
    guild_id: str,
    channel_id: str,
    title: str,
    description: str,
    color: str,
    thumbnail_url: Optional[str],
    image_url: Optional[str],
    footer_text: Optional[str],
    roles: List[Dict[str, str]]
):
    async with _lock:
        data = _load_data()
        for panel in data["panels"]:
            if panel["id"] == panel_id:
                panel["guild_id"] = guild_id
                panel["channel_id"] = channel_id
                panel["title"] = title
                panel["description"] = description
                panel["color"] = color
                panel["thumbnail_url"] = thumbnail_url or ""
                panel["image_url"] = image_url or ""
                panel["footer_text"] = footer_text or ""
                panel["roles"] = roles or []
                break
        _save_data(data)

async def get_all_panels() -> List[Dict[str, Any]]:
    async with _lock:
        data = _load_data()
        return data.get("panels", [])

async def get_panel_by_id(panel_id: int) -> Optional[Dict[str, Any]]:
    async with _lock:
        data = _load_data()
        for panel in data.get("panels", []):
            if panel["id"] == panel_id:
                return panel
        return None

async def get_panel_by_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    async with _lock:
        data = _load_data()
        for panel in data.get("panels", []):
            if str(panel.get("message_id")) == str(message_id):
                return panel
        return None

async def delete_panel(panel_id: int):
    async with _lock:
        data = _load_data()
        data["panels"] = [p for p in data.get("panels", []) if p["id"] != panel_id]
        _save_data(data)
