import os
import pydantic


class ClanCredentials(pydantic.BaseModel):
    tag: str
    url: str
    officers: list[str,]
    webhook_players: str
    webhook_squadrons: str
    webhook_day: str
    webhook_leave: str


LEADERBOARD_URL = "https://warthunder.com/en/community/clansleaderboard/"

CLANS_DATA = {
    "SOFUA": {
        "tag": "SOFUA",
        "url": "https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine",
        "officers": [
            "Spiox_",
        ],
        "webhook_players": os.environ.get(
            "SOFUA_PLAYERS",
            "https://discord.com/api/webhooks/1104312032502759524/xcK4bI2gYJ3Z6WtP9rPiRIYLSuasw2ssmpS0Kh1Os8Dl6WxNnG8KVTsbZARswsOCWq2t",
        ),
        "webhook_squadrons": os.environ.get(
            "SOFUA_SQUADRONS",
            "https://discord.com/api/webhooks/1104312032502759524/xcK4bI2gYJ3Z6WtP9rPiRIYLSuasw2ssmpS0Kh1Os8Dl6WxNnG8KVTsbZARswsOCWq2t",
        ),
        "webhook_day": os.environ.get(
            "SOFUA_DAY",
            "https://discord.com/api/webhooks/1104312032502759524/xcK4bI2gYJ3Z6WtP9rPiRIYLSuasw2ssmpS0Kh1Os8Dl6WxNnG8KVTsbZARswsOCWq2t",
        ),
        "webhook_leave": os.environ.get(
            "SOFUA_LEAVERS",
            "https://discord.com/api/webhooks/1104312032502759524/xcK4bI2gYJ3Z6WtP9rPiRIYLSuasw2ssmpS0Kh1Os8Dl6WxNnG8KVTsbZARswsOCWq2t",
        ),
    }
}

EMOJI = {
    "increase": "<:small_green_triangle:996827805725753374>",
    "decrease": "🔻",
    "track_clan": ":star:",
    "all_clans": ":military_helmet:",
}

CLANS = [ClanCredentials(**clan) for clan in CLANS_DATA.values()]
