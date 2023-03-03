import os

try:
    WEBHOOK_PLAYERS = os.environ['WEBHOOK_PLAYERS']
    WEBHOOK_SQUADRONS = os.environ['WEBHOOK_SQUADRONS']
    WEBHOOK_DAY = os.environ['WEBHOOK_DAY']
    WEBHOOK_ABANDONED = os.environ['WEBHOOK_ABANDONED']
except KeyError as err:
    print(err, 'raise an error. \nYou must set the environment variables in config.py')

# Critical URL's. Don't change these.
LB_URLS = ["https://warthunder.com/en/community/clansleaderboard",
           "https://warthunder.com/en/community/clansleaderboard/page/2",
           "https://warthunder.com/en/community/clansleaderboard/page/3"]

# Tracked clan data
CLAN_URL = "https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine"
TRACKED_CLAN_NAME = 'SOFUA'
CLAN_LEADER = 'Spiox_'

# Emojis
EMOJI = {'increase': '<:small_green_triangle:996827805725753374>',
         'decrease': '🔻',
         'track_clan': ':star:',
         'all_clans': ':military_helmet:'}

# SQL Server Settings
DB_PATH = "WTDB.sqlite"
