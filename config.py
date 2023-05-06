import os
test = 'https://discord.com/api/webhooks/1104312032502759524/xcK4bI2gYJ3Z6WtP9rPiRIYLSuasw2ssmpS0Kh1Os8Dl6WxNnG8KVTsbZARswsOCWq2t'
WEBHOOK_PLAYERS = os.environ.get('WEBHOOK_PLAYERS', test)
WEBHOOK_SQUADRONS = os.environ.get('WEBHOOK_SQUADRONS', test)
WEBHOOK_DAY = os.environ.get('WEBHOOK_DAY', test)
WEBHOOK_ABANDONED = os.environ.get('WEBHOOK_ABANDONED', test)


# Critical URL's. Don't change these.
LB_URLS = ["https://warthunder.com/en/community/clansleaderboard",
           "https://warthunder.com/en/community/clansleaderboard/page/2",
           "https://warthunder.com/en/community/clansleaderboard/page/3"]

# Tracked clan data
CLAN_URL = "https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine"
TRACKED_CLAN = 'SOFUA'
CLAN_LEADER = 'Spiox_'

# Emojis
EMOJI = {'increase': '<:small_green_triangle:996827805725753374>',
         'decrease': '🔻',
         'track_clan': ':star:',
         'all_clans': ':military_helmet:'}

# SQL Server Settings
DB_PATH = "WTDB.sqlite"
