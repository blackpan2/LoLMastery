"""
Copyright 2016 George Herde

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from os import environ
import cassiopeia as cass
import sqlalchemy
from cassiopeia.type.core.common import LoadPolicy
from cassiopeia import riotapi
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from operator import itemgetter as i
from functools import cmp_to_key

__author__ = 'George Herde'

# ITERATION USING SESSION
Base = declarative_base()
global_session = 0


class BackendSummoner(Base):
    __tablename__ = 'Summoner'
    id = Column(Integer, primary_key=True)
    user = Column(String(20))
    level = Column(Integer)
    icon = Column(Integer)
    revision_date = Column(DateTime)

    def __repr__(self):
        return "<Summoner(username='%s', id='%i', level='%i', icon='%i', revision='%s')>" % (
            self.user, self.id, self.level, self.icon, self.revision_date)


class BackendChampion(Base):
    __tablename__ = 'Champion'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    title = Column(String(50))

    def __repr__(self):
        return "<Champion(name='%s', title='%s', id='%i')>" % (
            self.name, self.title, self.id)


class BackendMastery(Base):
    __tablename__ = 'Mastery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    summoner_id = Column(Integer, ForeignKey('Summoner.id'))
    champion_id = Column(Integer, ForeignKey('Champion.id'))
    level = Column(Integer)
    points = Column(Integer)
    since_last_level = Column(Integer)
    until_next_level = Column(Integer)
    last_played = Column(Integer)
    high_grade = Column(String(5))
    chest = Column(Boolean)

    def __repr__(self):
        return "<Mastery(summoner='%i', champion='%i', level='%i', points='%i', chest='%s')>" % (
            self.summoner_id, self.champion_id, self.level, self.points, self.chest)


def init():
    setup_sql_alchemy()
    setup_riot_api()
    print("init complete...")


def setup_sql_alchemy():
    # Uncomment next line and comment following line to print database calls to the console during runtime
    # engine = create_engine('sqlite:///./lib/backend.db', echo=True)
    engine = sqlalchemy.create_engine('sqlite:///./backend.db')

    # Construct a sessionmaker object
    # noinspection PyPep8Naming
    Session = sessionmaker()
    Session.configure(bind=engine)

    session = Session()

    # Create all the tables in the database
    Base.metadata.create_all(engine)

    global global_session
    global_session = session
    # print("database setup complete...")


def setup_riot_api():
    # Riot's League of Legends API developer key, stored in your environment for protection
    cass.riotapi.set_api_key(environ["DEV_KEY"])

    cass.riotapi.set_region("NA")  # Currently only support region is NA
    # Uncomment next line to print Riot API calls to the console during runtime
    # cass.riotapi.print_calls(True)

    cass.riotapi.set_load_policy(LoadPolicy.eager)
    cass.riotapi.set_rate_limits((1500, 10), (90000, 600))
    # print("api setup complete...")


def check_exists(item_type, item_id):
    return global_session.query(item_type).filter(item_type.id == item_id).first() is not None


def insert_summoner_controller(summoner_name):
    return insert_summoner(summoner_obj(summoner_name))


def insert_summoner(summoner_item):
    summoner_id = summoner_item.id
    summoner = BackendSummoner(id=summoner_id, user=summoner_item.name, level=summoner_item.level,
                               icon=summoner_item.profile_icon_id, revision_date=summoner_item.modify_date)
    if check_exists(BackendSummoner, summoner_id):
        old = global_session.query(BackendSummoner).filter(BackendSummoner.id == summoner_id).first()
        global_session.delete(old)
        global_session.commit()
        global_session.add(summoner)
        global_session.commit()
        return False
    else:
        global_session.add(summoner)
        global_session.commit()
        return True


def insert_champion(champion):
    api_champion = champion
    champion_id = api_champion.id
    champion = BackendChampion(id=champion_id, name=champion.name, title=champion.title)
    if check_exists(BackendChampion, champion_id):
        old = global_session.query(BackendChampion).filter(BackendChampion.id == champion_id).first()
        global_session.delete(old)
        global_session.commit()
        global_session.add(champion)
        global_session.commit()
    else:
        global_session.add(champion)
        global_session.commit()


def check_mastery_exists(summoner_id, champion_id):
    return global_session.query(BackendMastery).filter(BackendMastery.summoner_id == summoner_id) \
               .filter(BackendMastery.champion_id == champion_id).first() is not None


def insert_champion_mastery(summoner, champion_obj):
    # print("Started {0}...".format(champion_obj.name), end="")
    try:
        api_mastery = cass.riotapi.get_champion_mastery(summoner=summoner, champion=champion_obj)
        api_successful = True
    except cass.type.api.exception.APIError:
        print("500 Error status for {0}...".format(champion_obj.name))
        api_successful = False
    if api_successful:
        summoner_id = summoner.id
        champion_id = champion_obj.id
        mastery = BackendMastery(summoner_id=summoner_id, champion_id=champion_id, level=api_mastery.level,
                                 points=api_mastery.points, since_last_level=api_mastery.points_since_last_level,
                                 until_next_level=api_mastery.points_until_next_level,
                                 last_played=api_mastery.last_played,
                                 high_grade=api_mastery.highest_grade, chest=api_mastery.chest_granted)
        if check_mastery_exists(summoner_id, champion_id):
            old = global_session.query(BackendMastery).filter(BackendMastery.summoner_id == summoner_id).filter(
                BackendMastery.champion_id == champion_id).first()
            global_session.delete(old)
            global_session.commit()
            global_session.add(mastery)
            global_session.commit()
        else:
            global_session.add(mastery)
            global_session.commit()
            # print("Finished {0}...".format(champion_obj.name))
    return api_successful


def generate_mastery_controller(summoner_name):
    return generate_mastery(summoner_obj(summoner_name))


def generate_mastery(summoner_item):
    # Fill the database with the user's information
    # list_champions, summoner = generation_resources(summoner_name)
    list_champions = cass.riotapi.get_champions()
    print("Pulled summoner. Got {0}.".format(summoner_item.name))
    print("Generating champion mastery information")
    failed_updates = []
    for champ in list_champions:
        insert_champion(champ)
        if not insert_champion_mastery(summoner_item, champ):
            failed_updates.append(champ.name)
    return failed_updates


def select_summoner_champion_mastery_controller(summoner_name):
    return select_summoner_champion_mastery(summoner_obj(summoner_name))


def select_summoner_champion_mastery(summoner_item):
    # SELECT Champion.*, Mastery.* FROM Champion, Mastery, Summoner
    #   WHERE Summoner.id == Mastery.summoner_id
    #       AND Champion.id == Mastery.champion_id
    #       AND Summoner.user == 'blackpan2'; # Blackpan2 as an example
    unsorted_collection = []
    for item in global_session.query(BackendMastery).filter(BackendMastery.summoner_id == summoner_item.id).all():
        # noinspection PyDictCreation
        return_item = {}
        return_item['id'] = item.summoner_id
        return_item['summoner'] = summoner_item.name
        return_item['champion'] = global_session.query(BackendChampion).filter(
            BackendChampion.id == item.champion_id).one().name
        return_item['level'] = item.level
        return_item['points'] = item.points
        return_item['since_last_level'] = item.since_last_level
        return_item['until_next_level'] = item.until_next_level
        return_item['last_played'] = item.last_played
        return_item['high_grade'] = item.high_grade
        return_item['chest'] = item.chest
        unsorted_collection.append(return_item)
    return multi_key_sort(unsorted_collection, ['-points', 'champion'])


def cmp(a, b):
    return (a > b) - (a < b)


def multi_key_sort(items, columns):
    comparators = [((i(col[1:].strip()), -1) if col.startswith('-') else (i(col.strip()), 1)) for col in columns]

    def comparator(left, right):
        comparator_iter = (cmp(fn(left), fn(right)) * multi for fn, multi in comparators)
        return next((result for result in comparator_iter if result), 0)

    return sorted(items, key=cmp_to_key(comparator))


def summoner_obj(summoner_name):
    return cass.riotapi.get_summoner_by_name(name=summoner_name)


def main(summoner_name):
    init()
    summoner = summoner_obj(summoner_name)
    new = insert_summoner(summoner)
    if new:
        generate_mastery(summoner)
    result = select_summoner_champion_mastery(summoner)
    print(result)


def main_controller(summoner_name):
    init()
    new = insert_summoner_controller(summoner_name)
    if new:
        generate_mastery_controller(summoner_name)
    result = select_summoner_champion_mastery_controller(summoner_name)
    print(result)


if __name__ == "__main__":
    main_controller("blackpan2")
