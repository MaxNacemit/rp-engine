from flask import Flask
from database import Database

app = Flask(__name__)

db = Database('root', 'strongsqlpassword')
db.register_user('shar3nda', 'stronguserpassword')
print(db.get_user_dict('shar3nda'))


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
