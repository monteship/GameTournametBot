from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DATE
from sqlalchemy.orm import Session
import os

from sqlalchemy.orm.attributes import get_history

from .items import PlayerItem, ClanItem

Base = declarative_base()


class PlayersTable(Base):
    __tablename__ = 'players'
    nick = Column(String, primary_key=True)
    rating = Column(Integer)
    activity = Column(Integer)
    role = Column(String)
    date_joined = Column(DATE)
    changes = Column(String)

    def __init__(self, nick, rating, activity, role, date_joined, changes=None):
        self.nick = nick
        self.rating = rating
        self.activity = activity
        self.role = role
        self.date_joined = date_joined
        self.changes = changes

    def __repr__(self):
        return "<PlayerItem %s, %s, %s, %s, %s, %s)>" % \
            (self.nick, self.rating, self.activity, self.role, self.date_joined, self.changes)


class LeaderBoardTable(Base):
    __tablename__ = 'leaderboard'
    tag = Column(String, primary_key=True)
    rank = Column(Integer)
    name = Column(String)
    members = Column(Integer)
    rating = Column(Integer)
    kills_to_death = Column(Integer)
    changes = Column(String)

    def __init__(self, tag, rank, name, members, rating, kills_to_death, changes=None):
        self.tag = tag
        self.rank = rank
        self.name = name
        self.members = members
        self.rating = rating
        self.kills_to_death = kills_to_death
        self.changes = changes

    def __repr__(self):
        return "<LeaderBoardItem %s, %s, %s, %s, %s, %s, %s)>" % \
            (self.tag, self.rank, self.name, self.members, self.rating, self.kills_to_death, self.changes)


class WtStatsScraperPipeline:
    def __init__(self):
        basename = 'wtstats.sqlite'
        self.engine = create_engine("sqlite:///%s" % basename, echo=False)
        if not os.path.exists(basename):
            Base.metadata.create_all(self.engine)

    def process_item(self, item, spider):
        if isinstance(item, PlayerItem):
            pt = PlayersTable(
                nick=item['nick'],
                rating=item['rating'],
                activity=item['activity'],
                role=item['role'],
                date_joined=item['date_joined'])
            self.session.add(pt)
            if self.session.is_modified(pt, include_collections=False):
                for attr in ['rating']:
                    history = get_history(pt, attr)
                    if history.has_changes():
                        changes = f', '.join(str(change) for change in history.deleted + history.added)
                        setattr(pt, 'changes', changes)

        if isinstance(item, ClanItem):
            lbt = LeaderBoardTable(
                tag=item['tag'],
                rank=item['rank'],
                name=item['name'],
                members=item['members'],
                rating=item['rating'],
                kills_to_death=item['kills_to_death'])
            self.session.add(lbt)
            if self.session.is_modified(lbt, include_collections=False):
                for attr in ['rank', 'members', 'rating', 'kills_to_death']:
                    history = get_history(lbt, attr)
                    if history.has_changes():
                        changes = ', '.join(str(change) for change in history.deleted + history.added)
                        setattr(lbt, 'changes', changes)
        return item

    def close_spider(self, spider):
        self.session.commit()
        self.session.close()

        players_changes = self.session.query(PlayersTable).filter(PlayersTable.changes.isnot(None)).all()
        if players_changes:
            message = "PlayersTable changes:\n"
            for player in players_changes:
                message += f"__{player.nick}__\nChanges: {player.changes}\n"

    def open_spider(self, spider):
        self.session = Session(bind=self.engine)
