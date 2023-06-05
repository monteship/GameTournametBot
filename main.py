import os
import time

import schedule

from background import keep_alive
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class ScheduleSpiders:

    def __init__(self):
        self.process = CrawlerProcess(get_project_settings())
        self.schedule = schedule
        self.schedule_daily_leader_board_parsing()
        self.schedule_daily_players_parsing()

    def schedule_daily_leader_board_parsing(self):
        self.schedule.every().day.at("22:15").do(
            lambda: os.system('scrapy crawl LeaderBoardStats -a table_name=squadrons_daily'))

        clans_parsing_time = [f"{hour}:{minute}" for hour in range(15, 23) for minute in ["00", "30"]]
        for parsing_time in clans_parsing_time:
            self.schedule.every().day.at(parsing_time).do(
                lambda: os.system('scrapy crawl LeaderBoardStats -a table_name=squadrons_instant'))

    def schedule_daily_players_parsing(self):
        self.schedule.every().day.at("22:16").do(
            lambda: os.system('scrapy crawl PlayerStats -a table_name=players_daily'))

        self.schedule.every().minute.do(
            lambda: os.system('scrapy crawl PlayerStats -a table_name=players_instant'))

    def start(self):
        keep_alive()
        while True:
            self.schedule.run_pending()
            self.process.start()
            print('Sleeping for 30 seconds...')
            time.sleep(30)


if __name__ == '__main__':
    scheduler = ScheduleSpiders()
    scheduler.start()
