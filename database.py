import sqlite3


def create_databases():
    db_path = "WTDB.db"
    db = sqlite3.connect(db_path, check_same_thread=False)
    sql = db.cursor()
    sql.execute(
        '''
        CREATE TABLE IF NOT EXISTS "players" 
        ("name" INTEGER,
        "rank" INTEGER,
        "points" INTEGER)
        ''')
    db.commit()
    sql.execute(
        '''
        CREATE TABLE IF NOT EXISTS "squadrons" 
        ("name" TEXT,
        "rank" INTEGER,
        "points" INTEGER,
        "kills" INTEGER,
        "deaths" INTEGER,
        "players" INTEGER)
        ''')
    db.commit()
    sql.execute(
        '''
        CREATE TABLE IF NOT EXISTS "period_squadrons" 
        ("name" TEXT,
        "rank" INTEGER,
        "points" INTEGER,
        "kills" INTEGER,
        "deaths" INTEGER,
        "players" INTEGER)
        ''')
    db.commit()
    sql.close()
