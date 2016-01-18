# -*- coding:utf-8 -*-
__author__ = u'东方鹗'


from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField, SelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(Form):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(6, 64, message=u'邮件长度要在6和64之间'),
                        Email(message=u'邮件格式不正确！')])
    password = PasswordField(u'密码', validators=[DataRequired()])
    remember_me = BooleanField(label=u'记住我', default=False)
    submit = SubmitField(u'登 录')


class RegisterForm(Form):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(6, 64, message=u'邮件长度要在6和64之间'),
                        Email(message=u'邮件格式不正确！')])
    username = StringField(u'用户名', validators=[DataRequired(), Length(1, 16, message=u'用户名长度要在1和16之间'),
                           Regexp(ur'^[\u4E00-\u9FFF]+$', flags=0, message=u'用户名必须为中文')])
    password = PasswordField(u'密码', validators=[DataRequired(), EqualTo(u'password2', message=u'密码必须一致！')])
    password2 = PasswordField(u'重输密码', validators=[DataRequired()])
    submit = SubmitField(u'注 册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已被注册！')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已被注册！')


class ChangePasswordForm(Form):
    old_password = PasswordField(u'旧密码', validators=[DataRequired()])
    password = PasswordField(u'密码', validators=[DataRequired(), EqualTo(u'password2', message=u'密码必须一致！')])
    password2 = PasswordField(u'重输密码', validators=[DataRequired()])
    submit = SubmitField(u'更新密码')


class PasswordResetRequestForm(Form):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(6, 64, message=u'邮件长度要在6和64之间'),
                        Email(message=u'邮件格式不正确！')])
    submit = SubmitField(u'发送')


class PasswordResetForm(Form):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(6, 64, message=u'邮件长度要在6和64之间'),
                        Email(message=u'邮件格式不正确！')])
    password = PasswordField(u'密码', validators=[DataRequired(), EqualTo(u'password2', message=u'密码必须一致！')])
    password2 = PasswordField(u'重输密码', validators=[DataRequired()])
    submit = SubmitField(u'确认')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'邮箱未注册！')


class ChangeEmailForm(Form):
    email = StringField(u'新邮箱', validators=[DataRequired(), Length(6, 64, message=u'邮件长度要在6和64之间'),
                        Email(message=u'邮件格式不正确！')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField(u'更新邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已被注册！！')


class ChangeUsernameForm(Form):
    username = StringField(u'用户名', validators=[DataRequired(), Length(1, 64, message=u'用户名长度要在1和64之间'),
                           Regexp(ur'^[\u4E00-\u9FFF]+$', flags=0, message=u'用户名必须为中文')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField(u'更新昵称')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已被注册！')


class EditRealUserForm(Form):
    name = StringField(u'真实姓名', validators=[DataRequired(), Length(1, 64, message=u'姓名长度要在1和64之间'),
                       Regexp(ur'^[\u4E00-\u9FFF]+$', flags=0, message=u'用户名必须为中文')])
    picture = FileField(u'头像图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], u'只能上传jpg, jpeg, png格式的图片')
    ])
    phone = StringField(u'电话', validators=[DataRequired(), Length(11, 11, message=u'电话号码必须为11位'),
                        Regexp(ur'^[0-9]+$', flags=0, message=u'电话号码必须为数字')])
    about_me = TextAreaField(u'个人简介')
    submit = SubmitField(u'修改资料')


class EditUserForm(Form):
    user_id = StringField()
    name = StringField(u'真实姓名', validators=[DataRequired(), Length(1, 64, message=u'姓名长度要在1和64之间'),
                       Regexp(ur'^[\u4E00-\u9FFF]+$', flags=0, message=u'用户名必须为中文')])
    picture = FileField(u'头像图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], u'只能上传jpg, jpeg, png格式的图片')
    ])
    phone = StringField(u'电话', validators=[DataRequired(), Length(11, 11, message=u'电话号码必须为11位'),
                        Regexp(ur'^[0-9]+$', flags=0, message=u'电话号码必须为数字')])
    about_me = TextAreaField(u'个人简介')
    role_id = SelectField(u'权限', coerce=int)
    disabled = SelectField(u'状态', choices=[(u'True', u'注销'), (u'False', u'正常') ])
    submit = SubmitField(u'修改资料')


class SearchUserForm(Form):
    search = StringField(u'搜索用户')
    submit = SubmitField(u'搜索')


class ArticleForm(Form):
    title = StringField(u'文章标题', validators=[DataRequired(), Length(1, 64, message=u'文章标题长度要在1和64之间')])
    body_html = StringField(u'文章内容', validators=[DataRequired(message=u'文章内容必须填写')])
    submit = SubmitField(u'确认')


class AdoptPostForm(Form):
    pass


class RejectPostForm(Form):
    title = StringField(u'拒绝理由', validators=[DataRequired(), Length(1, 64, message=u'标题长度要在1和64之间')])
    content = TextAreaField(u'内容')
    submit = SubmitField(u'确认')


class OffPostForm(Form):
    post_id = StringField(validators=[DataRequired()])


class AdoptAlbumForm(Form):
    pass


class RejectAlbumForm(Form):
    title = StringField(u'拒绝理由', validators=[DataRequired(), Length(1, 64, message=u'标题长度要在1和64之间')])
    content = TextAreaField(u'内容')
    submit = SubmitField(u'确认')


class OffAlbumForm(Form):
    post_id = StringField(validators=[DataRequired()])


class DeleteMessageForm(Form):
    message_id = StringField()


class AllReadMessageForm(Form):
    pass


class MessageForm(Form):
    checkbox = BooleanField(default=False)
    read = BooleanField(default=False)
    check_delete = BooleanField(default=False)


class RejectAlbumForm(Form):
    title = StringField(u'拒绝理由', validators=[DataRequired(), Length(1, 64, message=u'标题长度要在1和64之间')])
    content = TextAreaField(u'内容')
    submit = SubmitField(u'确认')


class OffAlbumForm(Form):
    album_id = StringField(validators=[DataRequired()])


class EditArticleForm(Form):
    title = StringField(u'文章标题', validators=[DataRequired(), Length(1, 64, message=u'文章标题长度要在1和64之间')])
    body_html = StringField(u'文章内容', validators=[DataRequired(message=u'文章内容必须填写')])
    submit = SubmitField(u'提交')


class AlbumForm(Form):
    title = StringField(u'专辑标题', validators=[DataRequired(), Length(1, 64, message=u'姓名长度要在1和64之间')])
    picture = FileField(u'专辑图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], u'只能上传jpg, jpeg, png格式的图片')
    ])
    percentage = RadioField(u'分成比例', choices=[('0', u'0'), ('0.05', u'5%'), ('0.1', u'10%'), ('0.15', u'15%'),
                                              ('0.2', u'20%'), ('0.25', u'25%'), ('0.3', u'30%')], default=0)
    introduction = TextAreaField(u'专辑简介')
    submit = SubmitField(u'提交')


class EditAlbumForm(Form):
    title = StringField(u'专辑标题', validators=[DataRequired(), Length(1, 64, message=u'姓名长度要在1和64之间')])
    picture = FileField(u'专辑图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], u'只能上传jpg, jpeg, png格式的图片')
    ])
    percentage = RadioField(u'分成比例', choices=[('0', u'0'), ('0.05', u'5%'), ('0.1', u'10%'),
                                                ('0.15', u'15%'), ('0.2', u'20%'), ('0.25', u'25%'), ('0.3', u'30%')])
    introduction = TextAreaField(u'专辑简介')
    submit = SubmitField(u'提交')


class ToRealForm(Form):
    name = StringField(u'真实姓名', validators=[DataRequired(), Length(1, 64, message=u'姓名长度要在1和64之间'),
                       Regexp(ur'^[\u4E00-\u9FFF]+$', flags=0, message=u'用户名必须为中文')])
    picture = FileField(u'头像图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], u'只能上传jpg, jpeg, png格式的图片')
    ])
    phone = StringField(u'电话', validators=[DataRequired(), Length(11, 11, message=u'电话号码必须为11位'),
                        Regexp(ur'^[0-9]+$', flags=0, message=u'电话号码必须为数字')])
    about_me = TextAreaField(u'个人简介')
    submit = SubmitField(u'提交资料')