from flask import Flask, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_restful import Api

from utilities import get_users, handle_connect, handle_disconnect, register_user, login_user, chat, logout_user, handle_message, send_message
from dbs import db
import configparser

# Initialize the Flask application
app = Flask(__name__)

# Load configuration from the config.cfg file
config = configparser.ConfigParser()
config.read('config.cfg')

app.config['SECRET_KEY'] = config['APP']['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = config['APP']['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy extension
db.init_app(app)


socketio = SocketIO(app)
api = Api(app)

# Set the initial route to '/login'
@app.route('/')
def initial():
    return redirect(url_for('login'))

# Routes
app.add_url_rule('/register', 'register', register_user, methods=['GET', 'POST'])
app.add_url_rule('/login', 'login', login_user, methods=['GET', 'POST'])
app.add_url_rule('/chat', 'chat', chat)
app.add_url_rule('/logout', 'logout', logout_user)
app.add_url_rule('/api/users', 'get_users', get_users)

# WebSocket event for handling messages
@socketio.on('connect')
def handle_socket_connect():
    handle_connect(socketio)
@socketio.on('disconnect')
def handle_socket_disconnect():
    handle_disconnect(socketio)
@socketio.on('message')
def handle_socket_message(data):
    send_message(socketio, data, session)

if __name__ == '__main__':
    socketio.run(app, debug=app.config.get('DEBUG', False))
