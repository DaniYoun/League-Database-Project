from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlite3 
from sqlite3 import Error

db = SQLAlchemy()
DB_NAME = "project.db"
database = r"project.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_Key'] = 'DANISDATABASE'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    
    from .views import views
    
    app.register_blueprint(views, url_prefix='/')
    
    from .models import Champions
    
    return app

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        return conn
    except Error as e:
        print(e)

    return conn

conn = create_connection(database)