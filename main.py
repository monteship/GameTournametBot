from threading import Thread
import time
import schedule
import timeit

from config import WEBHOOK_PLAYERS, PLAYERS_EMBED, DAY_START_EMBEDS, WEBHOOK_DAY, \
    DAY_START_EMBEDS, DAY_END_EMBEDS, WEBHOOK_SQUADRONS, SQUADRONS_PARSING_TIME
from player import parsing_players
from squadron import parsing_squadrons
from database import create_databases
from background import keep_alive


def parsing_players_thread():
    Thread(target=parsing_players,
           args=[WEBHOOK_PLAYERS, *PLAYERS_EMBED]).start()


def parsing_squadrons_day_start_thread():
    Thread(
        target=parsing_squadrons,
        args=[WEBHOOK_DAY, "period_squadrons",
              *DAY_START_EMBEDS]).start()


def parsing_squadrons_day_end_thread():
    Thread(target=parsing_squadrons,
           args=[WEBHOOK_DAY, "period_squadrons",
                 *DAY_END_EMBEDS]).start()


def parsing_squadrons_thread():
    Thread(
        target=parsing_squadrons,
        args=[WEBHOOK_SQUADRONS, "squadrons",
              *DAY_START_EMBEDS]).start()


def time_checker():
    hours = time.gmtime().tm_hour + 2
    minutes = time.gmtime().tm_min
    curr_time = str(hours * 60 + minutes)
    print(curr_time)
    if curr_time in SQUADRONS_PARSING_TIME:
        print("Parsing Squadrons")
        start = timeit.default_timer()
        parsing_squadrons_thread()
        print(f"Parsing Squadrons in {timeit.default_timer() - start}")
    elif curr_time == '960':  # Run at 16:00 GMT+2
        print("Parsing Day Start")
        parsing_squadrons_day_start_thread()
    elif curr_time in ['1443']:  # Run at 00:05 GMT+2 next day
        print("Parsing Day End")
        parsing_squadrons_day_end_thread()
    parsing_players_thread()  # Run every 1 minute


if __name__ == '__main__':
    # Run in production
    try:
        keep_alive()
        create_databases()
        schedule.every(60).seconds.do(time_checker)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Manually stopped")
    except Exception as e:
        print(e)
