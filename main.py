from threading import Thread
import time
import schedule
import config
from player import parsing_players
from squadron import parsing_squadrons
from database import create_databases
from background import keep_alive


def parsing_players_thread():
    Thread(target=parsing_players,
           args=[config.WEBHOOK_PLAYERS, *config.PLAYERS_EMBED]).start()


def parsing_squadrons_day_start_thread():
    Thread(
        target=parsing_squadrons,
        args=[config.WEBHOOK_DAY, "period_squadrons",
              *config.DAY_START_EMBEDS]).start()


def parsing_squadrons_day_end_thread():
    Thread(target=parsing_squadrons,
           args=[config.WEBHOOK_DAY, "period_squadrons",
                 *config.DAY_END_EMBEDS]).start()


def parsing_squadrons_thread():
    Thread(
        target=parsing_squadrons,
        args=[config.WEBHOOK_SQUADRONS, "squadrons",
              *config.DAY_START_EMBEDS]).start()


def time_checker():
    a = (str(
        str(
            int(time.strftime('%H', time.gmtime())) * 60 +
            (int(time.strftime('%M', time.gmtime()))))))
    print(a)
    if a in [
        '110', '140', '170', '200', '230', '260', '290', '320', '350', '380',
        '410', '860', '890', '920', '950', '980', '1010', '1040', '1070', '1100',
        '1130', '1160', '1190', '1220', '1250', '1280', '1310'
    ]:
        parsing_squadrons_thread()
    elif a == '830':
        parsing_squadrons_day_start_thread()
    elif a in ['440', '1340']:  # 440 , 1340
        parsing_squadrons_day_end_thread()
    parsing_players_thread()


if __name__ == '__main__':
    # Run in production
    keep_alive()
    create_databases()
    schedule.every(60).seconds.do(time_checker)
    while True:
        schedule.run_pending()
        time.sleep(1)
