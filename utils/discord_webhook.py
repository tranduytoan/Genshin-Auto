import os
import requests
from typing import Optional
from user_stats import get_user_stats


def send_discord_notification(content: str) -> bool:
    """
    Send notification to Discord webhook with user stats and content
    
    Args:
        content (str): Main content message to send
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL environment variable not found")
        return False
    user_data = get_user_stats()
    message = _build_message(content, user_data)
    payload = {
        "content": message,
        "username": "Genshin Auto Daily Bot",
        "avatar_url": "https://i.imgur.com/AfFp7pu.png"
    }
    
    if user_data:
        payload["embeds"] = [_create_embed(content, user_data)]
        payload["content"] = "" 
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("Discord notification sent successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Discord notification: {e}")
        return False


def _build_message(content: str, user_data: Optional[dict]) -> str:
    """
    Build message content with user personalization
    
    Args:
        content (str): Main content
        user_data (dict): User stats data
        
    Returns:
        str: Formatted message
    """
    if not user_data:
        return f"**Genshin Impact Auto Daily**\n\n{content}"
    
    nickname = user_data.get('nickname', 'Traveler')
    level = user_data.get('level', '?')
    
    return f"**Genshin Impact Auto Daily**\n👤 Player: **{nickname}** (AR {level})\n\n{content}"


def _create_embed(content: str, user_data: dict) -> dict:
    """
    Create Discord embed with user stats and content
    
    Args:
        content (str): Main content
        user_data (dict): User stats data
        
    Returns:
        dict: Discord embed object
    """
    nickname = user_data.get('nickname', 'Traveler')
    level = user_data.get('level', '?')
    region = user_data.get('region', '?')
    game_head_icon = user_data.get('game_head_icon', 'https://genshin.hoyoverse.com/favicon.ico')
    
    if isinstance(level, int):
        if level >= 55:
            color = 0xFFD700  # Gold
        elif level >= 45:
            color = 0x9932CC  # Purple
        elif level >= 35:
            color = 0x4169E1  # Blue
        elif level >= 25:
            color = 0x32CD32  # Green
        else:
            color = 0x808080  # Gray
    else:
        color = 0x5865F2  # Discord blurple
    
    player_info = f"**Adventure Rank:** {level}"
    if region and region.strip():
        player_info += f"\n**Region:** {region}"
    
    embed = {
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
            "text": "Genshin Auto Daily Bot",
            "icon_url": "https://genshin.hoyoverse.com/favicon.ico"
        },
        "timestamp": _get_current_timestamp()
    }
    
    return embed


def _get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format for Discord embed
    
    Returns:
        str: Current timestamp
    """
    from datetime import datetime
    return datetime.utcnow().isoformat()
