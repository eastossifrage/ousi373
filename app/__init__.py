# -*- coding:utf-8 -*-
__author__ = u'东方鹗'


from flask import Flask
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from config import config


mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    """ 使用工厂函数初始化程序实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app=app)

    mail.init_app(app=app)
    moment.init_app(app=app)
    db.init_app(app=app)
    login_manager.init_app(app=app)

    # 注册蓝本 main
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # 注册蓝本 auth
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # 注册蓝本 markdown
    from .markdown import markdown as markdown_blueprint
    app.register_blueprint(markdown_blueprint, url_prefix='/markdown')

    return app
