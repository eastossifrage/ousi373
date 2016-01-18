# -*- coding:utf-8 -*-
__author__ = u'东方鹗'

from flask import render_template
from . import markdown


@markdown.route('/', methods=['GET', 'POST'])
def index():

    return render_template('markdown/index.html')