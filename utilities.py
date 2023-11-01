from flask import request, session, redirect, url_for, render_template
from flask_login import current_user
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import datetime
from flask_restful import Resource, reqparse
from flask import jsonify

from models import Users, Messages
from dbs import db


bcrypt = Bcrypt()



def get_users():
    users = Users.query.all()
    users_data = [{'username': user.username} for user in users]
    return jsonify(users_data)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = Users(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

def login_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session.permanent = True
            session['user'] = username
            return redirect(url_for('chat'))

    return render_template('login.html')

def chat():
    return render_template('chat.html')

def logout_user():
    session.pop('user', None)
    return redirect(url_for('login'))

def handle_message(socketio, message):
    user = Users.query.filter_by(username=session['user']).first()
    new_message = Messages(content=message, user_id=user.id)
    db.session.add(new_message)
    db.session.commit()

    socketio.emit('message', {'content': message, 'timestamp': new_message.timestamp, 'sender': session['user']}, broadcast=True)

# Function to get messages for the current user
def get_user_messages():
    user = Users.query.filter_by(username=session['user']).first()
    messages = Messages.query.filter_by(user_id=user.id).all()
    return messages

# Function to get all users except the current user
def get_all_users():
    users = Users.query.filter(Users.username != session['user']).all()
    return users

class MessageResource(Resource):
    @login_required
    def get(self):
        messages = Messages.query.filter_by(user_id=current_user.id).all()
        return [message.serialize() for message in messages]

    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('content', type=str, required=True, help='Content is required')
        args = parser.parse_args()

        new_message = Messages(
            content=args['content'],
            timestamp=datetime.now(),
            user_id=current_user.id
        )
        db.session.add(new_message)
        db.session.commit()
        return new_message.serialize(), 201
