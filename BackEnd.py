from os import environ
import sqlalchemy
from sqlalchemy import exc
import cassiopeia as cass
from cassiopeia.type.core.staticdata import Champion

__author__ = 'George Herde'


def insert_summoner(summoner_name):
    summoner = cass.riotapi.get_summoner_by_name(name=summoner_name)
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
        print("Champion added to database.")
        result.close()
    except exc.IntegrityError:
        # pass
        print("Champion already in database")


def insert_champion_mastery(summoner, champ):
    engine, summoner_table, champion_table, mastery_table = setup_sql_alchemy()
    from cassiopeia.type.core.staticdata import Champion
    if isinstance(champ, Champion):
        try:
            champ_mastery = cass.riotapi.get_champion_mastery(summoner=summoner, champion=champ)
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
        except cass.type.api.exception.APIError:
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
    summoner = cass.riotapi.get_summoner_by_name(name=summoner_name)
    list_champions = cass.riotapi.get_champions()
    return list_champions, summoner


def select_summoner_champion_mastery(summoner_name):
    engine, summoner_table, champion_table, mastery_table = setup_sql_alchemy()
    # SELECT Champion.*, Mastery.* FROM Champion, Mastery, Summoner
    #   WHERE Summoner.id == Mastery.summoner_id
    #       AND Champion.id == Mastery.champion_id
    #       AND Summoner.user == 'blackpan2'; # Blackpan2 as an example
    s = sqlalchemy.select([champion_table, mastery_table]). \
        where(sqlalchemy.and_(summoner_table.c.user == summoner_name,
                              summoner_table.c.id == mastery_table.c.summoner_id,
                              champion_table.c.id == mastery_table.c.champion_id)). \
        order_by(sqlalchemy.desc(mastery_table.c.points), sqlalchemy.asc(champion_table.c.name))
    conn = engine.connect()
    result = conn.execute(s)

    return_collection = []
    for row in result:
        return_collection.append([row['name'], row['level'], row['points']])

    result.close()
    return return_collection


def setup_sql_alchemy():
    # Uncomment next line and comment following line to print database calls to the console during runtime
    # engine = create_engine('sqlite:///./lib/backend.db', echo=True)
    engine = sqlalchemy.create_engine('sqlite:///./backend.db')
    metadata = sqlalchemy.MetaData()
    summoners = sqlalchemy.Table('Summoner', metadata,
                                 sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                 sqlalchemy.Column('user', sqlalchemy.String(20)),
                                 sqlalchemy.Column('level', sqlalchemy.Integer),
                                 sqlalchemy.Column('icon', sqlalchemy.Integer),
                                 sqlalchemy.Column('revision_date', sqlalchemy.Integer),
                                 )
    champion = sqlalchemy.Table('Champion', metadata,
                                sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                sqlalchemy.Column('name', sqlalchemy.String(20)),
                                sqlalchemy.Column('title', sqlalchemy.String(25)),
                                )
    mastery = sqlalchemy.Table('Mastery', metadata,
                               sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True),
                               sqlalchemy.Column('summoner_id', None, sqlalchemy.ForeignKey('Summoner.id')),
                               sqlalchemy.Column('champion_id', None, sqlalchemy.ForeignKey('Champion.id')),
                               sqlalchemy.Column('level', sqlalchemy.Integer),
                               sqlalchemy.Column('points', sqlalchemy.Integer),
                               sqlalchemy.Column('since_last_level', sqlalchemy.Integer),
                               sqlalchemy.Column('until_next_level', sqlalchemy.Integer),
                               sqlalchemy.Column('last_played', sqlalchemy.Integer),
                               sqlalchemy.Column('high_grade', sqlalchemy.String(5)),
                               sqlalchemy.Column('chest', sqlalchemy.String(5)),
                               )
    metadata.create_all(engine)
    # print("database setup complete...")
    return engine, summoners, champion, mastery


def setup_riot_api():
    # Riot's League of Legends API developer key, stored in your environment for protection
    cass.riotapi.set_api_key(environ["DEV_KEY"])

    cass.riotapi.set_region("NA")  # Currently only support region is NA
    # Uncomment next line to print Riot API calls to the console during runtime
    # cass.riotapi.print_calls(True)

    cass.riotapi.set_load_policy(cass.type.core.common.LoadPolicy.eager)
    cass.riotapi.set_rate_limits((1500, 10), (90000, 600))
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
