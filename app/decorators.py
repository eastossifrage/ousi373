# -*- coding:utf-8 -*-
__author__ = u'东方鹗'


from flask import current_app, abort, url_for, redirect
from threading import Thread
from functools import wraps
from flask.ext.login import current_user
from models import Permission
from werkzeug.utils import secure_filename
import hashlib
import random
import string
import os
import datetime


def async(f):
    """ 多线程修饰器 """
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def confirmed_required(f):
    """
    账户必须通过邮件确认
    :param f: 函数
    :return:
    """
    @wraps(f)
    def confirmed_function(*args, **kwargs):
        if current_user.confirmed is True:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('auth.unconfirmed'))
    return confirmed_function


def permission_required(permission):
    """ 检查常规权限 """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """ 检查管理员权限 """
    return permission_required(Permission.ADMINISTER)(f)


def upload(f, folder):
    """
    :param f: 文件名
    :return:
    """
    if f:
        app = current_app._get_current_object()
        file_name = hashlib.new(name='md5', string=('%s%s' % (current_user.id, secure_filename(f.filename).
                                                              rsplit('.', 1)[0]))).hexdigest()
        file_extension = f.filename.rsplit('.', 1)[1]
        filename = '%s.%s' % (file_name, file_extension)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], folder, filename))
    else:
        filename = None
    return filename
