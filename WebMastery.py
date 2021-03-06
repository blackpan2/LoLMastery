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

from os import urandom
from flask import Flask, request, redirect, url_for, render_template, session, flash
import BackEnd as BackEnd

app = Flask(__name__)
app.secret_key = urandom(24)


@app.route('/', methods=['GET'])
def show_home():
    BackEnd.init()
    session['init_complete'] = True
    session['static_data'] = ""
    return render_template('home.html')


@app.route('/search', methods=['GET', 'POST'])
def search_summoner():
    if not session.get('init_complete'):
        BackEnd.init()
        session['init_complete'] = True
    if request.method == 'POST':
        if request.form['summoner_name'] == "":
            return render_template('search.html')
        session['summoner_name'] = request.form['summoner_name']
        session['if_new'] = BackEnd.insert_summoner_controller(session['summoner_name'])
        if session['if_new']:
            failed = BackEnd.generate_mastery_controller(session['summoner_name'])
            for champion in failed:
                flash(champion + " failed to update, please retry")
        return redirect(url_for('show_mastery', summoner_name=session['summoner_name']))
    # show the form, it wasn't submitted
    return render_template('search.html')


@app.route('/mastery/<summoner_name>', methods=['GET', 'POST'])
def show_mastery(summoner_name):
    if not session.get('init_complete'):
        BackEnd.init()
        session['init_complete'] = True
    session['summoner_name'] = summoner_name
    if request.method == 'POST':
        BackEnd.generate_mastery_controller(summoner_name)
        flash('Mastery Updated')
        return redirect(url_for('show_mastery', summoner_name=session['summoner_name']))
    session['mastery_data'], summoner = BackEnd.select_summoner_champion_mastery_controller(summoner_name)
    session['static_data'] = BackEnd.static_data_controller()
    session['icon_url'] = 'http://ddragon.leagueoflegends.com/cdn/' + str(
        session['static_data']['version']) + '/img/profileicon/' + str(summoner.icon) + '.png'
    return render_template('mastery.html', session=session)


@app.route('/champion/<champion_key>', methods=['GET', 'POST'])
def show_detail(champion_key):
    if not session.get('init_complete'):
        BackEnd.init()
        session['init_complete'] = True
    session['champion_data'] = BackEnd.select_champion(champion_key=champion_key)
    return render_template('mastery_detail.html', session=session)


if __name__ == '__main__':
    app.debug = True
    app.run()
