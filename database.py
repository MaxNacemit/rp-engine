import mysql.connector


class database():
	def __init__(self, login, password):
		server = mysql.connector.connect(host="localhost", user=login, password=password)
		server.cursor().execute("CREATE DATABASE IF NOT EXISTS database")
		self.cursor = mysql.connector.connect(host="localhost", user=login, password=password, database="database").cursor()
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spells (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), public BOOLEAN, obvious BOOLEAN, descripion_file VARCHAR(100), school VARCHAR(8))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spell_reqs (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), spell INT FOREIGN KEY REFERENCES spells(id), dependence VARCHAR(3))') #dependence is mul(*), div, msq(*x^2), dsq or exp
		self.cursor.execute('CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCRMENT PRIMARY KEY, name VARCHAR(50), learning_const REAL, school VARCHAR(8), biography_file VARCHAR(50))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS beasts (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), danger_class INT, description_file VARCHAR(50))')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS spells_knowledge(user_id INT FOREIGN KEY REFERENCES users(id), spell_id INT FOREIGN KEY REFERENCES spells(id))')
	

