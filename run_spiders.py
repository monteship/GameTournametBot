from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl("PlayerStats", table_name="players_instant")
    # process.crawl("LeaderBoardStats", table_name="squadrons_instant")

    process.start()
