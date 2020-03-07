import mysql.connector
import hashlib


class database():
	def __init__(self, login, password):
		self.con = mysql.connector.connect(host="localhost", user=login, password=password, database="database")
		self.cursor = self.con.cursor()
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spells (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), public BOOLEAN, obvious BOOLEAN, required_const REAL, mana_cost INT, descripion_file VARCHAR(100), school VARCHAR(8))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spell_reqs (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), spell INT FOREIGN KEY REFERENCES spells(id), dependence VARCHAR(3))') #dependence is mul(*), div, msq(*x^2), dsq or exp
		self.cursor.execute('CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCRMENT PRIMARY KEY, name VARCHAR(50), learning_const REAL, school VARCHAR(8), biography_file VARCHAR(50), pass_hash CHAR(128), status INT, max_mana INT)') #пароли должны хешироваться SHA-512; статус - 3 - Admin, 2 - Master, 1 - User, 0 - непринятая анкета, -1 - Banned
		self.cursor.execute('CREATE TABLE IF NOT EXISTS beasts (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), danger_class INT, description_file VARCHAR(50))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spells_knowledge(user_id INT FOREIGN KEY REFERENCES users(id), spell_id INT FOREIGN KEY REFERENCES spells(id))')
		self.pending_con = mysql.connector.connect(host = "localhost", user = "pending", password = "password", database = "pending")
		self.pending.cur = self.pending_con.cursor()
		self.pending_cur.execute('CREATE TABLE IF NOT EXISTS pending_spells (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), public BOOLEAN, obvious BOOLEAN, required_const REAL, mana_cost INT, descripion_file VARCHAR(100), school VARCHAR(8))')
		self.pending_cur.execute('CREATE TABLE IF NOT EXISTS pending_spell_reqs (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), spell INT FOREIGN KEY REFERENCES pending_spells(id), dependence VARCHAR(3))')		
	
	def add_spell(self, spell_params, spell_variables): #Первое - кортеж (название, публичность, очевидность(=способность понять по описанию каста, что кастуется), требования по константе обученности, расход маны, адрес файла с описанием, школа)
		insert_request = 'INSERT INTO spells (name, public, obvious, required_const, mana_cost, description_file, school) VALUES (%s, %s, %s, %s, %s, %s, %s)'
		self.cursor.execute(insert_request, spell_params)
		self.cursor.commit()
		spell_id = self.cursor.lastrowid
		req_request = 'INSERT INTO spell_reqs (name, spell, dependence) VALUES (%s, %s, %s)'
		for req_set in spell_variables:
			self.cursor.execute(req_request, (req_set[0], spell_id, req_set[1])) #Как видно отсюда, переменные для заклинания передаются как массив кортежей вида (параметр, характер зависимости)
			self.cursor.commit()
		
	def get_user_dict(self, user_id):
		user_req = 'SELECT * FROM users WHERE id = %s'
		val = (user_id, ) 
		user = self.cursor.execute(user_req, val).fetchone()
		result = {'id': user[0], 'name': user[1], 'learning_const': user[2], 'school': user[3], 'biography_file': user[4], 'pass_hash': user[5], 'status': user[6], 'mana_max': user[7]}
		return result
	
	def get_user_spells(self, user_id):
		user = self.get_user_dict(user_id)
		pub_vals = (1, user['school'], user['learning_const'])
		pub_req = 'SELECT id FROM spells WHERE public = %s AND school = %s AND required_const < %s'
		public_spells = self.cursor.execute(pub_req, pub_vals).fetchall()
		priv_req = 'SELECT spell_id FROM spells_knowledge WHERE user_id = %s'
		priv_ids = self.cursor.execute(priv_req, (user[id], )).fetchall()
		spells = public_spells + priv_ids
		return spells
		
	def register_user(self, name, password, character_data=[0, 0, "none", "biography"]):
		request = 'INSERT INTO users (name, pass_hash, learning_const, max_mana, school, biography_file, status) VALUES (%s, %s, %s, %s, %s, %s, 0)'
		pass_hash = hashlib.sha512().update(password.encode("utf-8"))
		password = pass_hash.hexdigest()
		self.cursor.execute(request, (name, password, character_data[0], character_data[1], character_data[2]))
		self.cursor.commit()

	def modify_user(self, user_id, status):
		request = 'UPDATE users SET status = %s WHERE id = %s'
		self.cursor.execute(request, (user_id, status))
	
	
	
	
		
		