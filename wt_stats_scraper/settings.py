import os

test = 'https://discord.com/api/webhooks/1104312032502759524/xcK4bI2gYJ3Z6WtP9rPiRIYLSuasw2ssmpS0Kh1Os8Dl6WxNnG8KVTsbZARswsOCWq2t'

WEBHOOK_PLAYERS = os.environ.get('WEBHOOK_PLAYERS', test)
WEBHOOK_SQUADRONS = os.environ.get('WEBHOOK_SQUADRONS', test)
WEBHOOK_DAY = os.environ.get('WEBHOOK_DAY', test)
WEBHOOK_ABANDONED = os.environ.get('WEBHOOK_ABANDONED', test)

CLAN_URL = os.environ.get('CLAN_URL', 'https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine')
CLAN_LEADERS = ['Spiox_']
TRACKED_CLANS = ['SOFUA']
EMOJI = {'increase': '<:small_green_triangle:996827805725753374>',
         'decrease': '🔻',
         'track_clan': ':star:',
         'all_clans': ':military_helmet:'}

BOT_NAME = "wt_stats_scraper"
SPIDER_MODULES = ["wt_stats_scraper.spiders"]
NEWSPIDER_MODULE = "wt_stats_scraper.spiders"

# USER_AGENT = "SOFUA"

ROBOTSTXT_OBEY = False

TELNETCONSOLE_ENABLED = False

# SPIDER_MIDDLEWARES = {
#    "wt_stats_scraper.middlewares.WtStatsScraperSpiderMiddleware": 543,
# }


# DOWNLOADER_MIDDLEWARES = {
#    "wt_stats_scraper.middlewares.WtStatsScraperDownloaderMiddleware": 543,
# }


ITEM_PIPELINES = {
    "wt_stats_scraper.pipelines.WtStatsScraperPipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
