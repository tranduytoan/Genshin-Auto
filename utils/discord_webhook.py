import os
from datetime import datetime
from typing import Optional

import requests
from user_stats import get_user_stats

try:
    from constants import DISCORD_BOT_NAME, DISCORD_AVATAR_URL, GENSHIN_FAVICON_URL, LEVEL_COLORS, DEFAULT_COLOR
except ImportError:
    DISCORD_BOT_NAME = "Genshin Auto Bot"
    DISCORD_AVATAR_URL = "https://genshin.hoyoverse.com/favicon.ico"
    GENSHIN_FAVICON_URL = "https://genshin.hoyoverse.com/favicon.ico"
    LEVEL_COLORS = {55: 0xFFD700, 45: 0x9932CC, 35: 0x4169E1, 25: 0x32CD32, 0: 0x808080}
    DEFAULT_COLOR = 0x5865F2


def send_discord_notification(content: str) -> bool:
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        return False
        
    user_data = get_user_stats()
    message = _build_message(content, user_data)
    payload = {
        "content": message,
        "username": DISCORD_BOT_NAME,
        "avatar_url": DISCORD_AVATAR_URL
    }
    
    if user_data:
        payload["embeds"] = [_create_embed(content, user_data)]
        payload["content"] = "" 
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException:
        return False


def _build_message(content: str, user_data: Optional[dict]) -> str:
    if not user_data:
        return f"**Genshin Impact Auto Daily**\n\n{content}"
    
    nickname = user_data.get('nickname', 'Traveler')
    level = user_data.get('level', '?')
    
    return f"**Genshin Impact Auto Daily**\n👤 Player: **{nickname}** (AR {level})\n\n{content}"


def _create_embed(content: str, user_data: dict) -> dict:
    nickname = user_data.get('nickname', 'Traveler')
    level = user_data.get('level', '?')
    region = user_data.get('region', '?')
    game_head_icon = user_data.get('game_head_icon', GENSHIN_FAVICON_URL)
    
    color = _get_color_by_level(level)
    
    player_info = f"**Adventure Rank:** {level}"
    if region and region.strip():
        player_info += f"\n**Region:** {region}"
    
    return {
        "title": "Genshin Impact Auto Daily",
        "description": content,
        "color": color,
        "author": {
            "name": nickname,
            "icon_url": game_head_icon
        },
        "fields": [
            {
                "name": "👤 Player Info",
                "value": player_info,
                "inline": True
            }
        ],
        "footer": {
            "text": DISCORD_BOT_NAME,
            "icon_url": GENSHIN_FAVICON_URL
        },
        "timestamp": datetime.utcnow().isoformat()
    }


def _get_color_by_level(level) -> int:
    if isinstance(level, int):
        for min_level in sorted(LEVEL_COLORS.keys(), reverse=True):
            if level >= min_level:
                return LEVEL_COLORS[min_level]
    return DEFAULT_COLOR
