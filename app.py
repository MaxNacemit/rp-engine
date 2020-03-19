import re

from flask import Flask, render_template, request, redirect, url_for, session

from database import Database

STATUS_DICT = {3: 'админ', 2: 'мастер', 1: 'пользователь', 0: 'не назначен', -1: 'забанен'}
REQ_SPELL_LABELS = {'spell_title', 'spell_cost', 'learning_const', 'description', 'is_public', 'is_obvious'}

db = Database('ivan', 'strongsqlpassword')

app = Flask(__name__)
app.secret_key = 'very secret and reliable secret key'


# TODO: add decorators to check login on user-only pages


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
            msg = 'В логине нельзя использовать спец. сиволы!'
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
def home():
    if 'loggedin' in session:
        return render_template('base.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST':
            form = dict(request.form)
            form.pop('submit')
            form['is_public'] = 1 if 'is_public' in form.keys() else 0
            form['is_obvious'] = 1 if 'is_obvious' in form.keys() else 0
            if REQ_SPELL_LABELS.issubset(form):
                # TODO database
                base = []
                extra = []
                msg = 'Заклинание отправлено на модерацию!'
            else:
                msg = 'Заполните все параметры!'
        return render_template('submit.html', msg=msg)
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        account = db.get_user_dict(session['username'])
        account['status'] = STATUS_DICT[account['status']]
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))


# TODO: make a working edit_profile() function and .html file
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    return render_template('edit_profile.html')


if __name__ == '__main__':
    app.run()
