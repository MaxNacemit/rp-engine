import mysql.connector
from passlib.hash import pbkdf2_sha512

USER_DICT_LABELS = (
    'login', 'pass_hash', 'nickname', 'max_mana', 'learning_const', 'school', 'biography_file', 'status')


class Database:
    def __init__(self, login, password):
        self.con = mysql.connector.connect(host="localhost", user=login, password=password, database="knowledge")
        self.cursor = self.con.cursor()
        # пароли должны хешироваться SHA-512; статус - 3 - Admin, 2 - Master, 1 - User, -1 - Banned
        # dependence is mul(*), div, msq(*x^2), dsq or exp
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS spells (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), is_public BOOLEAN, obvious BOOLEAN, required_const REAL, mana_cost INT, description_file VARCHAR(100), school VARCHAR(8))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS spell_reqs (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), spell INT, FOREIGN KEY (spell) REFERENCES spells (id), dependence VARCHAR(3))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS users (login VARCHAR(50) PRIMARY KEY, pass_hash CHAR(130), nickname VARCHAR(50), max_mana INT, learning_const REAL, school VARCHAR(8), biography_file VARCHAR(50), status INT)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS beasts (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), danger_class INT, description_file VARCHAR(50))')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS spells_knowledge(user_login VARCHAR(50), spell_id INT, FOREIGN KEY (user_login) REFERENCES users (login), FOREIGN KEY(spell_id) REFERENCES spells (id))')

    def add_spell(self, spell_params, spell_variables):
        """

        :param spell_params: кортеж (название, публичность, очевидность(=способность понять по описанию каста, что кастуется), требования по константе обученности, расход маны, адрес файла с описанием, школа)
        :param spell_variables: массив кортежей вида (параметр, характер зависимости)
        """
        insert_request = 'INSERT INTO spells (name, is_public, obvious, required_const, mana_cost, description_file, school, approved) VALUES (%s, %s, %s, %s, %s, %s, %s, false)'
        self.cursor.execute(insert_request, spell_params)
        self.cursor.commit()
        spell_id = self.cursor.lastrowid
        req_request = 'INSERT INTO spell_reqs (name, spell, dependence) VALUES (%s, %s, %s)'
        for req_set in spell_variables:
            self.cursor.execute(req_request, (req_set[0], spell_id, req_set[1]))
            self.con.cursor.commit()

    def register_user(self, login, password, char_data=None):
        if char_data is None:
            char_data = [0, 0, "none_school", "biography"]

        pass_hash = pbkdf2_sha512.hash(password)
        check_available = 'SELECT * FROM users WHERE login = %s'
        self.cursor.execute(check_available, (login,))
        if self.cursor.fetchone() is None:
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
        result = dict(zip(USER_DICT_LABELS, user))
        return result

    def get_user_spells(self, user_login):
        user = self.get_user_dict(user_login)
        pub_vals = (1, user['school'], user['learning_const'])
        pub_req = 'SELECT id FROM spells WHERE is_public = %s AND school = %s AND required_const < %s AND approved=true'
        public_spells = self.cursor.execute(pub_req, pub_vals).fetchall()
        priv_req = 'SELECT spell_id FROM spells_knowledge WHERE login = %s'
        priv_ids = self.cursor.execute(priv_req, (user['id'],)).fetchall()
        spells = public_spells + priv_ids
        return spells

    def check_login(self, username, password):
        user_data = self.get_user_dict(username)
        return pbkdf2_sha512.verify(password, user_data['pass_hash'])

    def modify_user(self, user_id, status):
        request = 'UPDATE users SET status = %s WHERE id = %s'
        self.cursor.execute(request, (user_id, status))

    def approve_spell(self, spell_id):
        self.cursor.execute('UPDATE spells SET approved=true WHERE id = %s', (spell_id,))
