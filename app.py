import random
import re

from flask import Flask, render_template, request, redirect, url_for, session

from database import Database

STATUS_DICT = {3: 'админ', 2: 'мастер', 1: 'пользователь', 0: 'не назначен', -1: 'забанен'}

db = Database('ivan', 'strongsqlpassword')
# reg_response = db.register_user('shar3nda' + str(random.randint(0, 99999999)).zfill(8), 'stronguserpassword',
#                                 [322, 228, "none_sch", "biography"])
# if reg_response:
#     print(f'user {reg_response} registered')
# else:
#     print('name already taken')
# user_test_data = db.get_user_dict(reg_response)
# login1 = db.check_login(reg_response, 'stronguserpassword')
# login2 = db.check_login(reg_response, 'wronguserpassword')
# print(login1, login2)

# create the application object
app = Flask(__name__)
app.secret_key = 'very secret and reliable secret key'


# route for handling the login page logic
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    # Check if "username" and "password" POST requests exist (user submitted form)
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        account = db.check_login(username, password)
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['username'] = username
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Неправильный логин/пароль!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
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
            msg = 'Вы успешно зарегистрировались!'
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


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        account = db.get_user_dict(session['username'])
        account['status'] = STATUS_DICT[account['status']]
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST' and ('bio' in request.form or 'password' in request.form):
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
            msg = 'Вы успешно зарегистрировались!'
            session['loggedin'] = True
            session['username'] = username
            return redirect(url_for('home'))
    elif request.method == 'POST':
        msg = 'Введите логин и пароль!'

    return render_template('register.html', msg=msg)


if __name__ == '__main__':
    app.run(debug=True)


