"""Constants used across the Genshin Auto Daily application"""

# API URLs
CHECKIN_API_URL = "https://sg-hk4e-api.hoyolab.com/event/sol/sign"
REDEEM_API_URL = "https://public-operation-hk4e.hoyoverse.com/common/apicdkey/api/webExchangeCdkey"
USER_STATS_API_URL = "https://bbs-api-os.hoyolab.com/game_record/genshin/api/index"
WIKI_URL = "https://genshin-impact.fandom.com/wiki/Promotional_Code"

# Activity IDs
DAILY_CHECKIN_ACT_ID = "e202102251931481"

# Status codes
CHECKIN_SUCCESS_CODES = {0, -5003}
REDEEM_SUCCESS_CODES = {0, -2017, -1007, -2001}
RATE_LIMIT_CODE = -2016

# Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

CHECKIN_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://act.hoyolab.com",
    "Referer": "https://act.hoyolab.com/",
    **DEFAULT_HEADERS
}

# Discord
DISCORD_BOT_NAME = "Genshin Auto Bot"
DISCORD_AVATAR_URL = "https://cdn2.steamgriddb.com/icon_thumb/73e5080f0f3804cb9cf470a8ce895dac.png"
GENSHIN_FAVICON_URL = "https://cdn2.steamgriddb.com/icon_thumb/73e5080f0f3804cb9cf470a8ce895dac.png"

# Level colors for Discord embeds
LEVEL_COLORS = {
    55: 0xFFD700,  # Gold
    45: 0x9932CC,  # Purple
    35: 0x4169E1,  # Blue
    25: 0x32CD32,  # Green
    0: 0x808080,   # Gray
}
DEFAULT_COLOR = 0x5865F2  # Discord blurple
