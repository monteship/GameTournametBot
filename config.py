from discord_webhook import DiscordEmbed
import os

# URL's for the webhook
WEBHOOK_PLAYERS = os.environ['WEBHOOK_PLAYERS']
WEBHOOK_SQUADRONS = os.environ['WEBHOOK_SQUADRONS']
WEBHOOK_DAY = os.environ['WEBHOOK_DAY']
WEBHOOK_ABANDONED = os.environ['WEBHOOK_ABANDONED']

# Critical URL's. Don't change these.
LB_URLS = ["https://warthunder.com/en/community/clansleaderboard",
           "https://warthunder.com/en/community/clansleaderboard/page/2"]  # For parsing 40 clans
# add more LB_URLS if needed ,
#            "https://warthunder.com/en/community/clansleaderboard/page/3  # For additional 20 clans

# URL of your clan (crucial: eng version of site)
CLAN_URL = "https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine"
TRACKED_CLAN_NAME = 'SOFUA'
CLAN_LEADER = 'Spiox_'
SQUADRONS_PARSING_TIME = [
    '1020', '1050', '1080', '1110', '1140', '1170', '1200', '1230',
    '1260', '1290', '1320', '1350', '1380', '1410', '1440']  # Range: 17:00 GMT+2 -> 00:00 GMT+2 Interval: 00:30

EMOJI = {'increase': '<:small_green_triangle:996827805725753374>',
         'decrease': '🔻',
         'track_clan': ':star:',
         'all_clans': ':military_helmet:'}

ABANDONED_EMBEDS = [DiscordEmbed(title="Втрати на полі бою", color="ff0000", url=LB_URLS[0]), ]

# SQL Server Settings
DB_PATH = "WTDB.sqlite"
