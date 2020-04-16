import re
from functools import wraps
from os import getenv, environ

from flask import Flask, render_template, request, redirect, url_for, session

from database import Database

STATUS_DICT = {3: 'админ', 2: 'мастер', 1: 'пользователь', 0: 'не назначен', -1: 'забанен'}
REQ_SPELL_LABELS = ['spell_title', 'is_public', 'is_obvious', 'learning_const', 'mana_cost', 'description', 'school']
environ['KN_USERNAME'] = 'root'
environ['KN_PASSWORD'] = 'nacemit'
environ['FLASK_SECRET_KEY'] = 'verystrongandsecretkey'
db = Database(getenv('KN_USERNAME'), getenv('KN_PASSWORD'))

app = Flask(__name__)
app.secret_key = getenv('FLASK_SECRET_KEY')


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return wrapper


def master_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # print(f.__name__, args, kwargs)
        curr_user = db.get_user_dict(session['username'])
        if 'loggedin' not in session and curr_user['status'] <= 1:
            return redirect(url_for('home'))
        return f(*args, **kwargs)

    return wrapper


@app.route('/', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account = db.check_login(username, password)
        if account:
            session['loggedin'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            msg = 'Неправильный логин/пароль!'
    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account = db.is_available(username)
        if not account:
            msg = 'Аккаунт уже зарегистрирован!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'В логине нельзя использовать спец. символы!'
        elif len(password) < 8:
            msg = 'Выберите пароль не менее 8 знаков!'
        elif not username or not password:
            msg = 'Заполните все поля!'
        else:
            db.register_user(username, password)
            session['loggedin'] = True
            session['username'] = username
            return redirect(url_for('home'))
    elif request.method == 'POST':
        msg = 'Введите логин и пароль!'
    return render_template('register.html', msg=msg)


@app.route('/home')
@login_required
def home():
    return render_template('home.html', username=session['username'])


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    msg = ''
    if request.method == 'POST':
        form = dict(request.form)
        form['is_public'] = '1' if 'is_public' in form.keys() else '0'
        form['is_obvious'] = '1' if 'is_obvious' in form.keys() else '0'
        if set(REQ_SPELL_LABELS).issubset(set(form.keys())):
            base = [0, 0, 0, 0, 0, 0, 0]
            extra = []
            for key in form.keys():
                if key in REQ_SPELL_LABELS:
                    try:
                        base[REQ_SPELL_LABELS.index(key)] = form[key][1]#проверка на наш комп
                        base[REQ_SPELL_LABELS.index(key)] = form[key]
                    except:
                        base[REQ_SPELL_LABELS.index(key)] = form[key][0]
                else:
                    extra.append((key, form[key]))
            base = tuple(base)
            db.add_spell(base, extra)
            msg = "Заклинание отправлено на модерацию!"
        else:
            msg = "Заполните все поля!"
    return render_template('submit.html', msg=msg)


@app.route('/profile')
@login_required
def profile():
    account = db.get_user_dict(session['username'])
    account['status'] = STATUS_DICT[account['status']]
    return render_template('profile.html', account=account)


# TODO: make a working edit_profile() function and .html file
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    return render_template('edit_profile.html')


@app.route('/spells_pending/', defaults={'page': 0}, methods=['GET', 'POST'])
@app.route('/spells_pending/<page>', methods=['GET', 'POST'])
@master_required
def pending_spells(page):
    if db.get_unapproved_spells_pages():
        try:
            spell_list = db.get_unapproved_spells_pages()[int(page)]
        except:
            return redirect(url_for('spells_pending', page=0))
    else:
        spell_list = None
    return render_template('spell_approval.html', page=spell_list)


@app.route('/pending/<spell_id>', methods=['GET', 'POST'])
@master_required
def pending(spell_id):
    spell = db.get_spell_dict(spell_id)
    if spell:
        return render_template('spell.html', spell=spell)
    else:
        return redirect(url_for('home'))


# TODO improve spell moderation
@app.route('/approve/<spell_id>', methods=['GET', 'POST'])
@master_required
def approve(spell_id):
    form = dict(request.form)
    spell = db.get_spell_dict(spell_id)
    if spell and form['submitter'] == "approve":
        db.approve_spell(spell_id)
    elif spell and form['submitter'] == "delete":
        db.delete_spell(spell_id)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host="0.0.0.0")
