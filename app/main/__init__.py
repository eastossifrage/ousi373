# -*- coding:utf-8 -*-
__author__ = u'东方鹗'


from flask import Blueprint

main = Blueprint('main', __name__)
# 在末尾导入相关模块，是为了避免循环导入依赖，因为在下面的模块中还要导入蓝本main
from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
