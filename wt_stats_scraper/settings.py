WEBHOOK_PLAYERS = "https://discord.com/api/webhooks/1076967433186852994/pHOjc3Ta0_HxLHU0YlMtH7UfV-Xll_OLWIZKXxPJzIenqyq1m5fo4ZsmYT8i6MolwSBV"

WEBHOOK_SQUADRONS = "https://discord.com/api/webhooks/1076968282831196300/2AQp-OcXn0WvsbAeB60VCRyz7-kCZxqDe34uCPzM8CE4vEwVS1FEk05yLZj23Lb9xgwi"

WEBHOOK_DAY = "https://discord.com/api/webhooks/1076968357363978290/fWDFEuWdqTL5wUDhm8ZVIaNeNuRWDKCXll2IM2tsdqNW7HwBipSaTz1-iw91mF8Rov3l"

WEBHOOK_ABANDONED = "https://discord.com/api/webhooks/1078003366673788938/9zPfvY6fxy0bub5LbMOWaL5Za2lTAsd2Y4gbvH7F4YZetBTfRTj0pfR3sKA0kwwZKPba"


LEADERBOARD_URL = "https://warthunder.com/en/community/clansleaderboard/"
CLAN_URL = "https://warthunder.com/en/community/claninfo/Welcome%20to%20Ukraine"


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
