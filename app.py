import re
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session

from database import Database
from manaengine import ManaCounter

STATUS_DICT = {3: 'админ', 2: 'мастер', 1: 'пользователь', 0: 'не назначен', -1: 'забанен'}
REQ_SPELL_LABELS = ['spell_title', 'is_public', 'is_obvious', 'learning_const', 'mana_cost', 'description', 'school']

db = Database('root', 'nacemit')
mana_engine = ManaCounter()


app = Flask(__name__)
app.secret_key = 'getenv(FLASK_SECRET_KEY)'


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return wrapper


def approval_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        curr_user = db.get_user_dict(session['username'])
        if 'loggedin' not in session or curr_user['status'] < 1:
            return redirect(url_for(''))
        return f(*args, **kwargs)

    return wrapper


def master_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        curr_user = db.get_user_dict(session['username'])
        if 'loggedin' not in session or curr_user['status'] <= 1:
            return redirect(url_for(''))
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


@app.route('/home', defaults={'page': 0})
@app.route('/home/<page>')
@login_required
def home(page):
    master = db.get_user_dict(session['username'])['status'] > 1
    try:
        locations = db.get_locations_pages()[page]
    except IndexError:
        locations = db.get_locations_pages()[0]
    return render_template('home.html', username=session['username'], master=master, locations=locations)


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
                    try:
                        extra.append((key, form[key][1]))
                        extra.pop()
                        extra.append((key, form[key]))
                    except:
                        extra.append((key, form[key][0]))
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


@app.route('/location/<id>/<page>', methods=['GET', 'POST'], defaults={'page': 0})
@approval_required
def location(id, page):
    if request.method == 'POST':
        mana_engine.compute_post(id, session['username'], request.form['content'], request.form['spells'], db)
    try:
        posts = db.get_post_pages(id)[page]
    except IndexError:
        posts = None
    return render_template('location.html', posts=posts)


@app.route('/create_location', methods=['GET', 'POST'])
@master_required
def create_location():
    msg = ""
    if request.method == 'POST':
        if request.form['name'] and request.form['description']:
            db.create_location(request.form['name'], request.form['description'])
            for key in request.form.keys():
                if key not in ['name', 'description']:
                    mana_engine.attune_player(key, db.cursor.lastrowid)
            msg = "Локация успешно создана!"
        else:
            msg = "Заполните все параметры!"
    db.cursor.execute('SELECT * FROM users')
    player_list = db.cursor.fetchall()
    return render_template('create_location.html', msg=msg, players=player_list)


@app.route('/spells_pending/', defaults={'page': 0}, methods=['GET', 'POST'])
@app.route('/spells_pending/<page>', methods=['GET', 'POST'])
@master_required
def pending_spells(page):
    if db.get_unapproved_spells_pages():
        try:
            spell_list = db.get_unapproved_spells_pages()[int(page)]
        except IndexError:
            return redirect(url_for('spells_pending', page=0))
    else:
        spell_list = None
    return render_template('spell_approval.html', page=spell_list)


@app.route('/user/<user_login>', methods=['GET', 'POST'])
@master_required
def user(user_login):
    user_data = db.get_user_dict(user_login)
    master_status = db.get_user_dict(session['username'])['status']
    if request.method == 'POST':
        if request.form['user_action'] == 'ban' and user_data['status'] < master_status:
            db.modify_user(user_login, status=-1)
        elif request.form['user_action'] == 'admin' and master_status == 3:
            db.modify_user(user_login, status=3)
        elif request.form['user_action'] == 'master':
            db.modify_user(user_login, status=2)
        elif request.form['user_action'] == 'approve' and user_data['biography_file'] and user_data['status'] < 1:
            db.modify_user(user_login, status=1)
    if user_login == session['username']:
        return redirect(url_for('profile'))
    user_data['status'] = STATUS_DICT[user_data['status']]
    return render_template('profile.html', account=user_data, master=master_status)


@app.route('/pending/<spell_id>', methods=['GET', 'POST'])
@master_required
def pending(spell_id):
    spell = db.get_spell_dict(spell_id)
    if spell:
        return render_template('spell.html', spell=spell)
    else:
        return redirect(url_for('spells_pending'))


# TODO improve spell moderation
@app.route('/approve/<spell_id>', methods=['GET', 'POST'])
@master_required
def approve(spell_id):
    form = dict(request.form)
    spell = db.get_spell_dict(spell_id)
    if spell and form['submitter'] == ["approve"] or form['submitter'] == "approve":
        db.approve_spell(spell_id)
    elif spell and form['submitter'] == ["delete"] or form['submitter'] == "delete":
        db.delete_spell(spell_id)
    return redirect(url_for('spells_pending'))

# TODO add a system of artifacts(like spells, but no mana requirements and only have 1 owner)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
