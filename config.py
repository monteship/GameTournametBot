from discord_webhook import DiscordEmbed
import os

# URL's for the webhook
WEBHOOK_PLAYERS = os.environ['WEBHOOK_PLAYERS']
WEBHOOK_SQUADRONS = os.environ['WEBHOOK_SQUADRONS']
WEBHOOK_DAY = os.environ['WEBHOOK_DAY']
# WEBHOOK_ABANDONED = os.environ['WEBHOOK_ABANDONED']

# URL of your clan (crucial: eng version of site)
CLAN_URL = "https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine"
TRACKED_CLAN_NAME = '╖SOFUA╖'

# Embed's for the activity check
PLAYERS_EMBED = [DiscordEmbed(title="Active players", color='ff0000', url=CLAN_URL),
                 DiscordEmbed(title="Active players (2)", color='ff0000', url=CLAN_URL)]

# Critical URL's. Don't change these.
LB_URLS = ["https://warthunder.com/en/community/clansleaderboard",
           "https://warthunder.com/en/community/clansleaderboard/page/2",
           "https://warthunder.com/en/community/clansleaderboard/page/3"]

#  Embed's for the squadrons leaderboard
SQUAD_EMBEDS = [DiscordEmbed(title="Таблиця лідерів (1)", color="ff0000", url=LB_URLS[0]),
                DiscordEmbed(title="Таблиця лідерів (2)", color="ff0000", url=LB_URLS[1])]

# Embed's for the day notification
DAY_START_EMBEDS = [DiscordEmbed(title="Результати (Start)", color="ff0000", url=LB_URLS[0]),
                    DiscordEmbed(title="Результати (Start)", color="ff0000", url=LB_URLS[1])]
DAY_END_EMBEDS = [DiscordEmbed(title="Результати (End)", color="ff0000", url=LB_URLS[0]),
                  DiscordEmbed(title="Результати (End)", color="ff0000", url=LB_URLS[1])]

# SQL Server Settings
DB_PATH = "WTDB.db"

# CSS Select
# Squadron
CSS_KILLED_AIR = \
    "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(2)"
CSS_KILLED_GROUND = \
    "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(3)"
CSS_DEATHS = \
    "body#bodyRoot div.squadrons-profile__header-stat.squadrons-stat > ul:nth-child(2) > li:nth-child(4)"
CSS_PLAYERS_COUNT = "div#squadronsInfoRoot div.squadrons-info__content-wrapper > div:nth-child(2)"
CSS_POINTS = "body#bodyRoot div:nth-child(1) > div.squadrons-counter__value"
CSS_SQUAD_NAME = "div#squadronsInfoRoot div.squadrons-info__title"
