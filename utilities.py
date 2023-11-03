import json
from flask import redirect, request, session, render_template, jsonify, url_for
from flask_socketio import emit
from functools import wraps
from flask_bcrypt import Bcrypt
from datetime import datetime

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

def handle_connect(socketio):
    username = session['user']
    emit('user_connected', username, broadcast=True)

def handle_disconnect(socketio):
    username = session['user']
    emit('user_disconnected', username, broadcast=True)

def handle_message(socketio, message):
    user = Users.query.filter_by(username=session['user']).first()
    new_message = Messages(content=message, user_id=user.id)
    db.session.add(new_message)
    db.session.commit()

    socketio.emit('message', {
        'content': message,
        'timestamp': new_message.timestamp,
        'sender': session['user']
    }, broadcast=True)

def get_recipient_user():
    # Replace this with your logic to select a recipient user
    recipient = Users.query.filter(Users.username != session['user']).first()
    if recipient:
        return recipient.username
    return None

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(o)

def send_message(socketio, data, session):
    recipient = data['recipient']
    content = data['content']

    sender_user = Users.query.filter_by(username=session['user']).first()
    recipient_user = Users.query.filter_by(username=recipient).first()

    if sender_user and recipient_user:
        new_message = Messages(content=content, sender_id=sender_user.id, recipient_id=recipient_user.id, timestamp=datetime.now())
        db.session.add(new_message)
        db.session.commit()

        message_data = {
            'content': content,
            'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'sender': session['user']
        }

        # Use room-based communication to send the message to the recipient
        room = f'{sender_user.id}-{recipient_user.id}'
        socketio.emit('message', message_data, room=room)

