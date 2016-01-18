# -*- coding:utf-8 -*-
__author__ = u'东方鹗'


from flask.ext.wtf import Form
from wtforms import StringField, SelectField, BooleanField, SubmitField


class SubscribeForm(Form):
	pass


class CollectForm(Form):
	pass


class SearchForm(Form):
	value = StringField()