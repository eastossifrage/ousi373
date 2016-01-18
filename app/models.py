# -*- coding:utf-8 -*-
__author__ = u'东方鹗'

from . import db
from flask.ext.login import UserMixin, AnonymousUserMixin
from .import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
import hashlib
from datetime import datetime
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Permission(object):
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(64))
    content = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def sender(self):
        return User.query.get_or_404(self.sender_id)

    def __repr__(self):
        return '<Message %r>' % self.content


class Subscribe(db.Model):
    __tablename__ = 'subscribe'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Collect(db.Model):
    __tablename__ = 'collection'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            u'一般用户': (Permission.FOLLOW | Permission.COMMENT, False),
            u'认证用户': (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES , False),
            u'协管员': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES |
                     Permission.MODERATE_COMMENTS, False),
            u'超级管理员': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    picture_url = db.Column(db.String(128))
    phone = db.Column(db.String(11))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    albums = db.relationship('Album', backref='creator', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    sender = db.relationship('Message',
                             foreign_keys=[Message.sender_id],
                             backref=db.backref('sender', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')
    receiver = db.relationship('Message',
                               foreign_keys=[Message.receiver_id],
                               backref=db.backref('receiver', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    subscribes = db.relationship('Subscribe',
                               foreign_keys=[Subscribe.user_id],
                               backref=db.backref('subscribes', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    collects = db.relationship('Collect',
                               foreign_keys=[Collect.user_id],
                               backref=db.backref('collects', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['OUSI_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise ArithmeticError('非明文密码，不可读。')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password=password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_user(self):
        return Role.query.get(self.role_id).permissions == Permission.FOLLOW | \
                                                           Permission.COMMENT

    def is_real_user(self):
        return Role.query.get(self.role_id).permissions == Permission.FOLLOW | \
                                                           Permission.COMMENT | \
                                                           Permission.WRITE_ARTICLES

    def is_moderator(self):
        return Role.query.get(self.role_id).permissions == Permission.FOLLOW | \
                                                           Permission.COMMENT | \
                                                           Permission.WRITE_ARTICLES | \
                                                           Permission.MODERATE_COMMENTS

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='mm', rating='g'):
        if self.picture_url:
            return os.path.join('/static/uploads/user', self.picture_url)
        else:
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar'
            else:
                url = 'http://cn.gravatar.com/avatar'
            hash = self.avatar_hash or hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                url=url, hash=hash, size=size, default=default, rating=rating)

    @property
    def my_role(self):
        return Role.query.get_or_404(self.role_id)

    @property
    def my_posts(self):
        return Post.query.filter_by(author_id=self.id, confirmed=True, disabled=False).order_by(Post.timestamp.desc()).all()

    def send_message(self, user, title, content):
        s = Message(sender=self, receiver=user, title=title, content=content)
        db.session.add(s)

    def subscribe(self, album):
        if not self.is_subscribing(album=album):
            s = Subscribe(subscribes=self, subscribed=album)
            db.session.add(s)

    def unsubscirbe(self, album):
        s = self.subscribes.filter_by(album_id=album.id).first()
        if s:
            db.session.delete(s)

    def is_subscribing(self, album):
        return self.subscribes.filter_by(album_id=album.id).first() is not None

    def collect(self, post):
        if not self.is_collecting(post=post):
            c = Collect(collects=self, collected=post)
            db.session.add(c)

    def uncollect(self, post):
        c = self.collects.filter_by(post_id=post.id).first()
        if c:
            db.session.delete(c)

    def is_collecting(self, post):
        return self.collects.filter_by(post_id=post.id).first() is not None

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    id = 0


    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_user(self):
        return False

    def is_real_user(self):
        return False

    def is_moderator(self):
        return False

    def is_subscribing(self, album):
        return False

    def is_collecting(self, post):
        return False


login_manager.anonymous_user = AnonymousUser


class Album(db.Model):
    __tablename__ = 'albums'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, index=True)
    picture_url = db.Column(db.String(128))
    introduction = db.Column(db.String(256), index=True)
    percentage = db.Column(db.Float, default=0)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    posts = db.relationship('Post', backref='album', lazy='dynamic')
    subscribed = db.relationship('Subscribe',
                               foreign_keys=[Subscribe.album_id],
                               backref=db.backref('subscribed', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def is_creator(self, user):
        return self.creator_id == user.id

    @property
    def my_creator(self):
        return User.query.get_or_404(self.creator_id)

    @property
    def all_posts(self):
        page = request.args.get('page', 1, type=int)
        return Post.query.filter_by(album_id=self.id).order_by(Post.timestamp.desc()).paginate(page, error_out=False)

    @property
    def all_true_posts(self):
        page = request.args.get('page', 1, type=int)
        return Post.query.filter_by(album_id=self.id, confirmed=True, disabled=False).order_by(Post.timestamp.desc()).paginate(page, error_out=False)

    @property
    def unconfirmed_posts(self):
        return Post.query.filter_by(album_id=self.id, confirmed=False, disabled=False).order_by(Post.timestamp.desc()).all()

    def __repr__(self):
        return '<Album %r>' % self.title


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, index=True)
    body_html = db.Column(db.Text)
    price = db.Column(db.Float, default=0)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    collected = db.relationship('Collect',
                               foreign_keys=[Collect.post_id],
                               backref=db.backref('collected', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def is_author(self, user):
        return self.author_id == user.id

    @property
    def my_author(self):
        return User.query.get_or_404(self.author_id)

    def is_album(self, album):
        return self.album_id == album.id

    @property
    def my_album(self):
        return Album.query.get(self.album_id)

    @property
    def my_collected(self):
        return self.collected.count()

    def __repr__(self):
        return '<Post %r>' % self.title
