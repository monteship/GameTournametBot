import os

CLAN_URL = os.environ.get('CLAN_URL', 'https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine')

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
