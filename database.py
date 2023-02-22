import sqlite3
from config import DB_PATH


def create_databases():
    """
    Creates the database if it doesn't exist.'
    :return:
    """
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        sql = conn.cursor()
        sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "players" 
            ("name" INTEGER,
            "rank" INTEGER,
            "points" INTEGER)
            ''')
        sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "squadrons" 
            ("name" TEXT,
            "rank" INTEGER,
            "points" INTEGER,
            "k_d" INTEGER,
            "players" INTEGER)
            ''')
        sql.execute(
            '''
            CREATE TABLE IF NOT EXISTS "period_squadrons" 
            ("name" TEXT,
            "rank" INTEGER,
            "points" INTEGER,
            "k_d" INTEGER,
            "players" INTEGER)
            ''')
        conn.commit()
