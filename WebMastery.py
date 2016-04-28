from os import urandom
from flask import Flask, request, redirect, url_for, render_template, session, flash
import BackEnd as BackEnd

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('WEBMASTERY_SETTINGS', silent=True)
app.secret_key = urandom(24)


@app.route('/', methods=['GET'])
def show_home():
    BackEnd.init()
    return render_template('home.html')


@app.route('/search', methods=['GET', 'POST'])
def search_summoner():
    if request.method == 'POST':
        if request.form['summoner_name'] == "":
            return render_template('search.html')
        session['summoner_name'] = request.form['summoner_name']
        session['if_new'] = BackEnd.insert_summoner_controller(session['summoner_name'])
        if session['if_new']:
            failed = BackEnd.generate_mastery_controller(session['summoner_name'])
            for champion in failed:
                flash(champion + " failed to update, please retry")
        return redirect(url_for('show_mastery'))
    # show the form, it wasn't submitted
    return render_template('search.html')


@app.route('/mastery', methods=['GET', 'POST'])
def show_mastery():
    if request.method == 'POST':
        BackEnd.generate_mastery_controller(session['summoner_name'])
        flash('Mastery Updated')
        return redirect(url_for('show_mastery'))
    session['mastery_data'] = BackEnd.select_summoner_champion_mastery_controller(session['summoner_name'])
    return render_template('mastery.html', session=session)


if __name__ == '__main__':
    app.debug = True
    app.run()
