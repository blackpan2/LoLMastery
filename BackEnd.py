from os import environ

from cassiopeia import riotapi, type
from sqlalchemy import exc

__author__ = 'George Herde'


def insert_summoner(summoner_name):
    summoner = riotapi.get_summoner_by_name(name=summoner_name)
    engine, summoner_table, champion_table, mastery_table = setup_sql_alchemy()
    print(summoner.id)
    ins = summoner_table.insert().values(id=summoner.id, user=summoner.name, level=summoner.level,
                                         icon=summoner.profile_icon_id, revision_date=summoner.modify_date)
    try:
        conn = engine.connect()
        result = conn.execute(ins)
        print("Summoner added to database")
        new = True
        result.close()
    except exc.IntegrityError:
        print("Summoner already in database")
        new = False

    return new


def insert_champion(champion):
    engine, summoner_table, champion_table, mastery_table = setup_sql_alchemy()
    ins = champion_table.insert().values(id=champion.id, name=champion.name, title=champion.title)
    conn = engine.connect()
    try:
        result = conn.execute(ins)
        # print("Champion added to database.")
        result.close()
    except exc.IntegrityError:
        pass
        # print("Champion already in database")


def insert_champion_mastery(summoner, champ):
    engine, summoner_table, champion_table, mastery_table = setup_sql_alchemy()
    from cassiopeia.type.core.staticdata import Champion
    if isinstance(champ, Champion):
        try:
            champ_mastery = riotapi.get_champion_mastery(summoner=summoner, champion=champ)
            ins = mastery_table.insert().values(summoner_id=summoner.id, champion_id=champ.id,
                                                level=champ_mastery.level, points=champ_mastery.points,
                                                since_last_level=champ_mastery.points_since_last_level,
                                                until_next_level=champ_mastery.points_until_next_level,
                                                last_played=champ_mastery.last_played,
                                                high_grade=champ_mastery.highest_grade,
                                                chest=champ_mastery.chest_granted)
            conn = engine.connect()
            try:
                result = conn.execute(ins)
                # print("Champion Mastery entry added to database.")
                result.close()
            except exc.IntegrityError:
                from sqlalchemy.sql.elements import and_
                mastery_table.update(). \
                    where(and_(mastery_table.c.summoner_id == summoner.id,
                               mastery_table.c.champion_id == champ.id)). \
                    values(summoner_id=summoner.id, champion_id=champ.id, level=champ_mastery.level,
                           points=champ_mastery.points, since_last_level=champ_mastery.points_since_last_level,
                           until_next_level=champ_mastery.points_until_next_level,
                           last_played=champ_mastery.last_played,
                           high_grade=champ_mastery.highest_grade, chest=champ_mastery.chest_granted)
                # print("Champion Mastery already in database. Entry updated")
        except type.api.exception.APIError:
            print("Server 500 error retry later")
            # print("_______________________________________")


def generate_mastery(summoner_name):
    # Fill the database with the user's information
    list_champions, summoner = generation_resources(summoner_name)
    print("Pulled summoner. Got {0}.".format(summoner_name))
    print("Generating champion mastery information")
    for champ in list_champions:
        insert_champion(champ)
        insert_champion_mastery(summoner, champ)


def generation_resources(summoner_name):
    summoner = riotapi.get_summoner_by_name(name=summoner_name)
    list_champions = riotapi.get_champions()
    return list_champions, summoner


# def generation_manager(summoner_name, i):
#     list_champions, summoner = generation_resources(summoner_name)
#     generate_mastery_subset(i, summoner, list_champions)
#
#
# def generate_mastery_subset(i, summoner, list_champions):
#     print("Generating champion mastery subset {0}".format(i))
#     if i == 1:
#         start = 0
#     else:
#         start = int((i - 1) * round(len(list_champions) / 10, 2))
#     end = int(i * round(len(list_champions) / 10, 2))
#     list_champions = list_champions[start:end]
#     for champ in list_champions:
#         insert_champion(champ)
#         insert_champion_mastery(summoner, champ)
#     print("Finished generating champion mastery subset {0}".format(i))


def select_summoner_champion_mastery(summoner_name):
    engine, summoner_table, champion_table, mastery_table = setup_sql_alchemy()
    from sqlalchemy import select, desc, asc
    from sqlalchemy.sql.elements import and_
    s = select([champion_table, mastery_table]). \
        where(and_(summoner_table.c.user == summoner_name,
                   summoner_table.c.id == mastery_table.c.summoner_id,
                   champion_table.c.id == mastery_table.c.champion_id)). \
        order_by(desc(mastery_table.c.points), asc(champion_table.c.name))
    conn = engine.connect()
    result = conn.execute(s)

    return_collection = []
    for row in result:
        return_collection.append([row['name'], row['level'], row['points']])

    result.close()
    return return_collection


def setup_sql_alchemy():
    from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
    # engine = create_engine('sqlite:///./lib/backend.db', echo=True)
    engine = create_engine('sqlite:///./backend.db')
    metadata = MetaData()
    summoners = Table('Summoner', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('user', String(20)),
                      Column('level', Integer),
                      Column('icon', Integer),
                      Column('revision_date', Integer),
                      )
    champion = Table('Champion', metadata,
                     Column('id', Integer, primary_key=True),
                     Column('name', String(20)),
                     Column('title', String(25)),
                     )
    mastery = Table('Mastery', metadata,
                    Column('id', Integer, primary_key=True, autoincrement=True),
                    Column('summoner_id', None, ForeignKey('Summoner.id')),
                    Column('champion_id', None, ForeignKey('Champion.id')),
                    Column('level', Integer),
                    Column('points', Integer),
                    Column('since_last_level', Integer),
                    Column('until_next_level', Integer),
                    Column('last_played', Integer),
                    Column('high_grade', String(5)),
                    Column('chest', String(5)),
                    )
    metadata.create_all(engine)
    # print("database setup complete...")
    return engine, summoners, champion, mastery


def setup_riot_api():
    riotapi.set_region("NA")
    # riotapi.print_calls(True)
    key = environ["DEV_KEY"]  # DEV_KEY is an environmental variable with my API key
    riotapi.set_api_key(key)
    from cassiopeia.type.core.common import LoadPolicy
    riotapi.set_load_policy(LoadPolicy.eager)
    riotapi.set_rate_limits((1500, 10), (90000, 600))
    # print("api setup complete...")


def init():
    setup_sql_alchemy()
    setup_riot_api()
    print("init complete...")


def main(summoner_name):
    init()
    new = insert_summoner(summoner_name)
    if new:
        generate_mastery(summoner_name)
    result = select_summoner_champion_mastery(summoner_name)
    print(result)


if __name__ == "__main__":
    main("blackpan2")
