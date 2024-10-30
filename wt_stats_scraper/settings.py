import os

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_PLAYERS = os.environ.get("WEBHOOK_PLAYERS")
WEBHOOK_SQUADRONS = os.environ.get("WEBHOOK_SQUADRONS")
WEBHOOK_DAY = os.environ.get("WEBHOOK_DAY")
WEBHOOK_ABANDONED = os.environ.get("WEBHOOK_ABANDONED")

LEADERBOARD_URL = "https://warthunder.com/en/community/clansleaderboard/"
CLAN_URL = os.environ.get("CLAN_URL")

CLAN_LEADERS = ["Spiox_"]
TRACKED_CLAN = "SOFUA"
EMOJI = {
    "increase": "<:small_green_triangle:996827805725753374>",
    "decrease": "🔻",
    "track_clan": ":star:",
    "all_clans": ":military_helmet:",
}
DB_NAME = "wtstats.sqlite"
BOT_NAME = "wt_stats_scraper"
SPIDER_MODULES = ["wt_stats_scraper.spiders"]
NEWSPIDER_MODULE = "wt_stats_scraper.spiders"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
)

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
