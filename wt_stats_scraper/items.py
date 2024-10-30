import scrapy


class PlayerItem(scrapy.Item):
    nick = scrapy.Field(serializer=str)
    rating = scrapy.Field(serializer=int)
    activity = scrapy.Field(serializer=int)
    role = scrapy.Field(serializer=str)
    date_joined = scrapy.Field(serializer=str)


class ClanItem(scrapy.Item):
    rank = scrapy.Field(serializer=int)
    name = scrapy.Field(serializer=str)
    tag = scrapy.Field(serializer=str)
    members = scrapy.Field(serializer=int)
    rating = scrapy.Field(serializer=int)
    kills_to_death = scrapy.Field(serializer=float)
