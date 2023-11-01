from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_restful import Api

from utilities import get_users, login_required, register_user, login_user, chat, logout_user, handle_message, MessageResource
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

# Routes
app.add_url_rule('/register', 'register', register_user, methods=['GET', 'POST'])
app.add_url_rule('/login', 'login', login_user, methods=['GET', 'POST'])
app.add_url_rule('/chat', 'chat', chat)
app.add_url_rule('/logout', 'logout', logout_user)
app.add_url_rule('/api/users', 'get_users', get_users)
api.add_resource(MessageResource, '/api/messages')

# WebSocket event for handling messages
@socketio.on('message')
def handle_message_socketio(message):
    handle_message(socketio, message)

if __name__ == '__main__':
    socketio.run(app, debug=app.config.get('DEBUG', False))
