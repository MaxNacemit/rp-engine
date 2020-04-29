import mysql.connector
from passlib.hash import pbkdf2_sha512
USER_DICT_LABELS = (
    'login', 'pass_hash', 'nickname', 'max_mana', 'learning_const', 'school', 'biography_file', 'status')

SPELL_DICT_LABELS = (
'id', 'spell_title', 'is_public', 'is_obvious', 'learning_const', 'mana_cost', 'description', 'school', 'approved')


class Database:
    def __init__(self, login, password):
        self.con = mysql.connector.connect(host="localhost", user=login, password=password, database="knowledge")
        self.cursor = self.con.cursor()
        # пароли должны хешироваться SHA-512; статус - 3 - Admin, 2 - Master, 1 - User, -1 - Banned
        # dependence is mul(*), div, msq(*x^2), dsq or exp
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS spells (id INT AUTO_INCREMENT PRIMARY KEY, spell_title VARCHAR(100), is_public BOOLEAN, is_obvious BOOLEAN, learning_const REAL, mana_cost INT, description TEXT, school VARCHAR(8), approved BOOLEAN)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS spell_reqs (id INT AUTO_INCREMENT PRIMARY KEY, req_title VARCHAR(50), spell INT, FOREIGN KEY (spell) REFERENCES spells (id), dependence VARCHAR(3))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS users (login VARCHAR(50) PRIMARY KEY, pass_hash CHAR(130), nickname VARCHAR(50), max_mana INT, learning_const REAL, school VARCHAR(8), biography_file TEXT, status INT)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS beasts (id INT AUTO_INCREMENT PRIMARY KEY, beast_name VARCHAR(50), danger_class INT, description_file TEXT)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS spells_knowledge(user_login VARCHAR(50), spell_id INT, FOREIGN KEY (user_login) REFERENCES users (login), FOREIGN KEY(spell_id) REFERENCES spells (id))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS locations(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), description TEXT)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS forum_posts(author VARCHAR(50), datetime TIMESTAMP, location INT, content TEXT, id INT AUTO_INCREMENT PRIMARY KEY, FOREIGN KEY (author) REFERENCES users (login), FOREIGN KEY (location) REFERENCES locations(id))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS casts(id INT AUTO_INCREMENT PRIMARY KEY, spell INT, post INT, FOREIGN KEY (post) REFERENCES forum_posts(id), FOREIGN KEY (spell) REFERENCES spells (id))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS cast_params(cast_id INT, param_name VARCHAR(50), param_value REAL, FOREIGN KEY (cast_id) REFERENCES casts(id))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS compendium_articles(id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(50), article TEXT)')


    def add_spell(self, spell_params, spell_variables):
        """

        :param spell_params: кортеж (название, публичность, очевидность(=способность понять по описанию каста, что кастуется), требования по константе обученности, расход маны, адрес файла с описанием, школа)
        :param spell_variables: массив кортежей вида (параметр, характер зависимости)
        """
        insert_request = 'INSERT INTO spells (spell_title, is_public, is_obvious, learning_const, mana_cost, description, school, approved) VALUES (%s, %s, %s, %s, %s, %s, %s, false)'
        self.cursor.execute(insert_request, spell_params)
        self.con.commit()
        spell_id = self.cursor.lastrowid
        req_request = 'INSERT INTO spell_reqs (req_title, spell, dependence) VALUES (%s, %s, %s)'
        for req_set in spell_variables:
            self.cursor.execute(req_request, (req_set[0], spell_id, req_set[1]))
            self.con.commit()

    def delete_spell(self, spell_id):
        self.cursor.execute('DELETE FROM spell_reqs WHERE spell=%s', (int(spell_id),))
        self.cursor.execute('DELETE FROM spells WHERE id=%s', (int(spell_id), ))
        self.con.commit()

    def get_spell_dict(self, spell_id):
        self.cursor.execute('SELECT * FROM spells WHERE id=%s', (spell_id,))
        spell = self.cursor.fetchone()
        if spell:
            return dict(zip(SPELL_DICT_LABELS, spell))
        else:
            return None

    def get_spell_params(self, spell_id):
        self.cursor.execute('SELECT * FROM spell_reqs WHERE spell=%s', (spell_id,))
        params = self.cursor.fetchall()
        params_dict = dict()
        for p in params:
            params_dict[p[2]] = p[3]
        return params_dict

    def approve_spell(self, spell_id):
        req = 'UPDATE spells SET approved=1 WHERE id=%s'
        self.cursor.execute(req, (spell_id,))
        self.con.commit()

    def get_unapproved_spells_pages(self):
        self.cursor.execute('SELECT * FROM spells WHERE approved="false"')
        spells_list = self.cursor.fetchall()
        pages = []
        while spells_list:
            page = []
            for _ in range(10):
                try:
                    spell = spells_list.pop()
                    spell = self.get_spell_dict(spell[0])
                    if spell:
                        page.append(spell)
                    else:
                        break
                except IndexError:
                    break
            pages.append(page)
        return pages

    def is_available(self, login):
        check = 'SELECT * FROM users WHERE login = %s'
        self.cursor.execute(check, (login,))
        if self.cursor.fetchone() is None:
            return True
        return False

    def register_user(self, login, password, char_data=None):
        # TODO VK OAuth
        if char_data is None:
            char_data = [0, 0, "none", "biography"]

        pass_hash = pbkdf2_sha512.hash(password)
        if self.is_available(login):
            request = 'INSERT INTO users (login, pass_hash, nickname, max_mana, learning_const, school, biography_file, status) VALUES (%s, %s, %s, %s, %s, %s, %s, 0)'
            self.cursor.execute(request, (login, pass_hash, login, *char_data))
            self.con.commit()
            return login
        return False

    def get_user_dict(self, user_login):
        """

        :param user_login: login of desired user
        :return dict of user data with following keys: 'login', 'pass_hash', 'nickname', 'max_mana', 'learning_const', 'school', 'biography_file', 'status'
        """
        user_req = 'SELECT * FROM users WHERE login = %s'
        self.cursor.execute(user_req, (user_login,))
        user = self.cursor.fetchone()
        if user is not None:
            result = dict(zip(USER_DICT_LABELS, user))
            return result
        return None

    def get_user_spells(self, user_login):
        user = self.get_user_dict(user_login)
        pub_vals = (1, user['school'], user['learning_const'])
        pub_req = 'SELECT id FROM spells WHERE is_public = %s AND school = %s AND required_const < %s AND approved=true'
        public_spells = self.cursor.execute(pub_req, pub_vals).fetchall()
        priv_req = 'SELECT spell_id FROM spells_knowledge WHERE login = %s'
        priv_ids = self.cursor.execute(priv_req, (user['id'],)).fetchall()
        spells = public_spells + priv_ids
        return spells

    # TODO check if cast is available, edit after moderation
    def check_login(self, username, password):
        user_data = self.get_user_dict(username)
        if user_data is not None:
            return pbkdf2_sha512.verify(password, user_data['pass_hash'])

    def modify_user(self, login, **kwargs):
        request = 'UPDATE users SET status = %s WHERE login = %s'
        self.cursor.execute(request, (kwargs['status'], login))
        self.con.commit()

    def get_post(self, post_id):
        result = dict()
        self.cursor.execute('SELECT * FROM forum_posts WHERE id=%s')
        post = self.cursor.fetchone()
        result['post'] = {'author': post[0], 'time': post[1], 'content': post[3]}
        self.cursor.execute('SELECT * FROM casts WHERE post=%s', (post_id))
        spells = self.cursor.fetchall()
        for spell in spells:
            cast_id = spell[0]
            spell_title, obvious = self.get_spell_dict(spell[1])['spell_title'], self.get_spell_dict(spell[1])['obvious']
            self.cursor.execute('SELECT * FROM cast_reqs WHERE cast_id=%s', (cast_id, ))
            params = self.cursor.fetchall()
            result[spell_title] = list(map(lambda x: {x[1]: x[2]}, params))
            result[spell_title]['obvious'] = obvious
        return result

    def make_post(self, location, author, content, casts): #casts - массив словарей вида {spell: id, params: {param1: value1 ...}}
        self.cursor.execute('INSERT INTO forum_posts (author, location, content) VALUES (%s, %s, %s)', (author, location, content))
        self.con.commit()
        post_id = self.cursor.lastrowid
        for spell in casts:
            self.cursor.execute('INSERT INTO casts (spell, post) VALUES (%s, %s)', (spell['spell'], post_id))
            self.con.commit()
            cast = self.cursor.lastrowid
            for param in spell['params'].keys(): #стоимость заклинания вычисляется до запуска этой функции
                self.cursor.execute('INSERT INTO cast_params (cast_id, param_name, param_value) VALUES (%s, %s, %s)', (cast, param, spell['params'][param]))
                self.con.commit()

    def delete_post(self, post_id):
        self.cursor.execute('DELETE FROM forum_posts WHERE id=%s', (post_id, ))
        self.con.commit()

    def get_locations_pages(self):
        self.cursor.execute('SELECT * FROM locations')
        locations = list(map(lambda x: {'id': x[0], 'name': x[1], 'description': x[2]}, self.cursor.fetchall()))
        pages = []
        while locations:
            page = []
            for _ in range(10):
                try:
                    loc = locations.pop()
                    if loc:
                        page.append(loc)
                    else:
                        break
                except IndexError:
                    break
            pages.append(page)
        if not pages:
            pages = [[None]]
        return pages

    def get_post_pages(self, location):
        self.cursor.execute('SELECT * FROM forum_posts WHERE location=%s', (location,))
        posts = self.cursor.fetchall()
        pages = []
        while posts:
            page = []
            for _ in range(10):
                try:
                    post_id = posts.pop()[4]
                    post = self.get_post(post_id)
                    if post:
                        page.append(post)
                    else:
                        break
                except IndexError:
                    break
            pages.append(page)
        return pages

    def create_location(self, name, description):
        self.cursor.execute('INSERT INTO locations (name, description) VALUES (%s, %s)', (name, description))
        self.con.commit()



