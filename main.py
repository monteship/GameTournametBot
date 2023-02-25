import datetime
from threading import Thread
import time
import schedule
from pytz import timezone

from config import WEBHOOK_PLAYERS, PLAYERS_EMBEDS, DAY_START_EMBEDS, WEBHOOK_DAY, \
    DAY_START_EMBEDS, DAY_END_EMBEDS, WEBHOOK_SQUADRONS, SQUADRONS_PARSING_TIME, SQUAD_EMBEDS
from database import Database
from player import PlayersLeaderboardUpdater
from squadron import ClansLeaderboardUpdater
from background import keep_alive


def parsing_players_thread():
    Thread(target=PlayersLeaderboardUpdater,
           args=[WEBHOOK_PLAYERS, 'players',
                 PLAYERS_EMBEDS]).start()


def parsing_players_partial_thread():
    Thread(target=PlayersLeaderboardUpdater,
           args=[WEBHOOK_DAY, "period_players",
                 PLAYERS_EMBEDS]).start()


def parsing_squadrons_day_start_thread():
    Thread(target=ClansLeaderboardUpdater,
           args=[WEBHOOK_DAY, "period_squadrons",
                 DAY_START_EMBEDS]).start()


def parsing_squadrons_day_end_thread():
    Thread(target=ClansLeaderboardUpdater,
           args=[WEBHOOK_DAY, "period_squadrons",
                 DAY_END_EMBEDS]).start()


def parsing_squadrons_thread():
    Thread(target=ClansLeaderboardUpdater,
           args=[WEBHOOK_SQUADRONS, "squadrons",
                 SQUAD_EMBEDS]).start()


def time_checker():
    """
    Build time constant, check if it's time to start parsing
    """
    kiev_time = datetime.datetime.now(timezone('Europe/Kiev'))
    hours = kiev_time.hour
    minutes = kiev_time.minute
    current_time = str(hours * 60 + minutes)
    print(current_time)
    if current_time in SQUADRONS_PARSING_TIME:
        parsing_squadrons_thread()
    elif current_time == '960':  # Run at 16:00 GMT+2
        parsing_squadrons_day_start_thread()
    elif current_time in ['1443']:  # Run at 00:05 GMT+2 next day
        parsing_squadrons_day_end_thread()
        # parsing_players_partial_thread()
    parsing_players_thread()  # Run every 1 minute


def main():
    """
    Main function
    """
    try:
        keep_alive()
        with Database(initialize=True) as conn:
            conn.create_databases()
            print("Database created")
        schedule.every(60).seconds.do(time_checker)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Manually stopped")


if __name__ == '__main__':
    main()
