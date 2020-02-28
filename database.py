import mysql.connector


class database():
	def __init__(self, login, password):
		server = mysql.connector.connect(host="localhost", user=login, password=password)
		server.cursor().execute("CREATE DATABASE IF NOT EXISTS database")
		self.cursor = mysql.connector.connect(host="localhost", user=login, password=password, database="database").cursor()
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spells (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), public BOOLEAN, obvious BOOLEAN, required_const REAL, mana_cost INT, descripion_file VARCHAR(100), school VARCHAR(8))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spell_reqs (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), spell INT FOREIGN KEY REFERENCES spells(id), dependence VARCHAR(3))') #dependence is mul(*), div, msq(*x^2), dsq or exp
		self.cursor.execute('CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCRMENT PRIMARY KEY, name VARCHAR(50), learning_const REAL, school VARCHAR(8), biography_file VARCHAR(50), pass_hash CHAR(128))') #пароли должны хешироваться SHA-512
		self.cursor.execute('CREATE TABLE IF NOT EXISTS beasts (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), danger_class INT, description_file VARCHAR(50))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spells_knowledge(user_id INT FOREIGN KEY REFERENCES users(id), spell_id INT FOREIGN KEY REFERENCES spells(id))')
	
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
		result = {'id': user[0], 'name': user[1], 'learning_const': user[2], 'school': user[3], 'biography_file': user[4], 'pass_hash': user[5]}
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
		
		

