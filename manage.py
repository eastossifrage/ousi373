# -*- coding:utf-8 -*-
__author__ = u'东方鹗'

import os
from app import create_app, db
from app.models import User, Role, Album, Post, Message, Subscribe, Collect
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app=app)
migrate = Migrate(app=app, db=db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Album=Album, Post=Post, Message=Message,
                Subscribe=Subscribe, Collection=Collect)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """ 单元测试 """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(test=tests)

if __name__ == '__main__':
    manager.run()
