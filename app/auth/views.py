# -*- coding:utf-8 -*-
__author__ = u'东方鹗'

from flask import render_template, request, redirect, url_for, flash, make_response, abort, jsonify
from flask.ext.login import login_user, logout_user, login_required, current_user, current_app
from ..models import User, Album, Post, Message, Role, Collect, Subscribe
from .forms import LoginForm, RegisterForm, ChangePasswordForm, PasswordResetForm, PasswordResetRequestForm, \
    ChangeEmailForm, ChangeUsernameForm, EditRealUserForm, ToRealForm, ArticleForm, EditArticleForm, AlbumForm, \
    EditAlbumForm, AdoptPostForm, RejectPostForm, OffPostForm, AdoptAlbumForm, RejectAlbumForm, OffAlbumForm, \
    DeleteMessageForm, AllReadMessageForm, MessageForm, EditUserForm, SearchUserForm
from ..decorators import permission_required, admin_required, confirmed_required, upload
from ..import db
from ..email import send_email
from . import auth
import os
import re
import json
from ..ueditor import Uploader, List


@auth.route('/', methods=['GET', 'POST'])
@login_required
@confirmed_required
def index():

    return render_template('auth/index.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(prefix='login')
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data.strip()).first()
        if user is not None and user.verify_password(login_form.password.data.strip()) and not user.disabled:
            login_user(user=user, remember=login_form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        elif user.disabled:
            flash({'error': u'用户已被管理员注销！'})
        elif user is None:
            flash({'error': u'邮箱未注册！'})
        elif not user.verify_password(login_form.password.data.strip()):
            flash({'error': u'密码不正确！'})
    return render_template('auth/login.html', loginForm=login_form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm(prefix='register')
    if register_form.validate_on_submit():
        user = User(email=register_form.email.data.strip(),
                    username=register_form.username.data.strip(),
                    password=register_form.password.data.strip())
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(to=user.email, subject=u'请求确认你的账户', template='auth/email/confirm', user=user, token=token)
        flash(message=u'一封确认邮件已发至您的邮箱')
        login_user(user=user)
        return redirect(url_for('auth.confirming'))
    return render_template('auth/register.html', registerForm=register_form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'您已经成功的对您的账户进行了邮件确认。非常感谢！')
    else:
        flash(u'本链接已经失效或者过期。')
        return redirect(url_for('auth.unconfirmed'))
    return redirect(url_for('auth.confirmed'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(to=current_user.email, subject=u'请求确认你的账户',
               template='auth/email/confirm', user=current_user, token=token)
    flash(message=u'一封注册确认邮件已发至您的邮箱')
    return redirect(url_for('auth.confirming'))


@auth.route('/email/confirming')
@login_required
def confirming():
    return render_template('auth/email/confirming.html')


@auth.route('/email/confirmed')
@login_required
@confirmed_required
def confirmed():
    return render_template('auth/email/confirmed.html')


@auth.before_app_request
def before_request():
    if current_user.is_authenticated():
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/email/unconfirmed.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
@confirmed_required
def change_password():
    change_password_form = ChangePasswordForm(prefix='change_password')
    if change_password_form.validate_on_submit():
        if current_user.verify_password(change_password_form.old_password.data.strip()):
            current_user.password = change_password_form.password.data.strip()
            db.session.add(current_user)
            flash({'success': u'您的账户密码已修改成功！'})
        else:
            flash({'error': u'无效的旧密码！'})

    return render_template('auth/config/change_password.html', changePasswordForm=change_password_form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous():
        return redirect(url_for('main.index'))
    password_reset_request_form = PasswordResetRequestForm()
    if password_reset_request_form.validate_on_submit():
        user = User.query.filter_by(email=password_reset_request_form.email.data.strip()).first()
        if user:
            token = user.generate_reset_token()
            send_email(to=user.email, subject=u'重置密码',
                       user=user, token=token, template='auth/password/reset_password',
                       next=request.args.get('next'))
            flash(user.username)
            flash(u'一封重置密码的确认邮件已发至您的邮箱')
            flash(user.email)
            return redirect(url_for('auth.password_reset_confirming'))
        else:
            flash({'error':u'邮箱未注册！'})
    return render_template('auth/password/password_reset_.html', passwordResetRequestForm=password_reset_request_form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous():
        return redirect(url_for('main.index'))
    password_reset_form = PasswordResetForm()
    if password_reset_form.validate_on_submit():
        user = User.query.filter_by(email=password_reset_form.email.data.strip()).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, password_reset_form.password.data):
            flash(user.username)
            flash(u'您的账户密码已重置,请使用新密码登录！')
            return redirect(url_for('auth.password_reset_confirmed'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/password/password_reset.html', passwordResetForm=password_reset_form)


@auth.route('/password/confirming')
def password_reset_confirming():
    return render_template('auth/password/reset_password_confirming.html')


@auth.route('/password/confirmed')
def password_reset_confirmed():
    return render_template('auth/password/reset_password_confirmed.html')


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
@confirmed_required
def change_email_request():
    change_email_form = ChangeEmailForm(prefix='change_email')
    if change_email_form.validate_on_submit():
        if current_user.verify_password(change_email_form.password.data):
            new_email = change_email_form.email.data.strip()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, u'更新邮箱',
                       'auth/email/change_email_',
                       user=current_user, token=token)
            flash({'success': u'一封确认邮件已发至您的邮箱'})
        else:
            flash({'error': u'密码错误！'})

    return render_template("auth/config/change_email.html", changeEmailForm=change_email_form)


@auth.route('/change-email/<token>')
@login_required
@confirmed_required
def change_email(token):
    if current_user.change_email(token):
        flash({'success': u'您的账户绑定邮箱已更新成功！'})
    else:
        flash({'error': u'无效的操作请求！'})
    return redirect(url_for('auth.config'))


@auth.route('/change-username', methods=['GET', 'POST'])
@login_required
@confirmed_required
def change_username():
    change_username_form = ChangeUsernameForm(prefix='change_username')
    if change_username_form.validate_on_submit():
        if current_user.verify_password(change_username_form.password.data):
            current_user.username = change_username_form.username.data.strip()
            db.session.add(current_user)
            flash({'success': u'昵称更新成功！'})
        else:
            flash({'error': u'密码错误！'})
    return render_template('auth/config/change_username.html', changeUsernameForm=change_username_form)


@auth.route('/edit-real-user', methods=['GET', 'POST'])
@login_required
@confirmed_required
def edit_real_user():
    edit_real_user_form = EditRealUserForm(obj=current_user, prefix='edit_real_user')
    if edit_real_user_form.validate_on_submit():
        current_user.name = edit_real_user_form.name.data.strip()
        current_user.phone = edit_real_user_form.phone.data.strip()
        current_user.about_me = edit_real_user_form.about_me.data.strip()
        app = current_app._get_current_object()
        if current_user.picture_url and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'],  'user', current_user.picture_url)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],  'user', current_user.picture_url))
        current_user.picture_url = upload(f=edit_real_user_form.picture.data, folder='user')
        flash({'success': u'用户资料修改成功！'})

    return render_template('auth/user-edit/real-user.html', editRealUserForm=edit_real_user_form)


@auth.route('/to-real', methods=['GET', 'POST'])
@login_required
@confirmed_required
def to_real():
    to_real_form = ToRealForm(prefix='to_real')
    if to_real_form.validate_on_submit():
        current_user.name = to_real_form.name.data.strip()
        current_user.phone = to_real_form.phone.data.strip()
        current_user.about_me = to_real_form.about_me.data.strip()
        app = current_app._get_current_object()
        if current_user.picture_url and \
                os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], 'user', current_user.picture_url)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'user', current_user.picture_url))
        current_user.picture_url = upload(f=to_real_form.picture.data, folder='user')
        flash({'success': u'申请材料已提交，请等候管理员审核。'})

    return render_template('auth/role/to-real.html', toRealForm=to_real_form)


@auth.route('/my_articles', methods=['GET', 'POST'])
@login_required
@confirmed_required
def my_articles():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.timestamp.desc()).paginate(page, error_out=False)
    off_post_form = OffPostForm(prefix='off_post')
    if off_post_form.validate_on_submit():
        p = Post.query.get_or_404(int(off_post_form.post_id.data.strip()))
        p.disabled = True

    return render_template('auth/articles/my-articles.html', posts=posts, offPostForm=off_post_form)


@auth.route('/<int:album_id>/write_article', methods=['GET', 'POST'])
@login_required
@confirmed_required
def write_article(album_id):
    a = Album.query.get_or_404(album_id)
    if current_user != a.creator and not (current_user.is_administrator() or current_user.is_moderator()):
        abort(403)
    article_form = ArticleForm(prefix='article')
    if article_form.validate_on_submit():
        if current_user._get_current_object() is a.creator:
            p = Post(title=article_form.title.data.strip(), body_html=article_form.body_html.data.strip(), album=a,
                     author=current_user._get_current_object(), confirmed=True)
        else:
            p = Post(title=article_form.title.data.strip(), body_html=article_form.body_html.data.strip(), album=a,
                     author=current_user._get_current_object())
        db.session.add(p)
        current_user.send_message(user=a.creator, title=u'新文章需经过您的审核',
                                  content=u'<p>《%s》已由%s提交与专辑《%s》发表，</p>' % (p.title, current_user, a.title))
        return redirect(url_for('main.album', album_id=a.id))

    return render_template('auth/articles/write-article.html', articleForm=article_form)


@auth.route('/edit_article/<int:post_id>', methods=['GET', 'POST'])
@login_required
@confirmed_required
def edit_article(post_id):
    p = Post.query.get_or_404(post_id)
    if current_user != p.author and not (current_user.is_administrator() or current_user.is_moderator()):
        abort(403)
    edit_article_form = EditArticleForm(prefix='edit_article')
    if edit_article_form.validate_on_submit():
        p.title = edit_article_form.title.data.strip()
        p.body_html = edit_article_form.body_html.data.strip()
        if p.my_author is not p.my_album.my_creator:
            p.confirmed = False
        return redirect(url_for('main.post', post_id=p.id))

    return render_template('auth/articles/edit-article.html', post=p, editArticleForm=edit_article_form)


@auth.route('/<int:album_id>/manage_articles', methods=['GET', 'POST'])
@login_required
@confirmed_required
def manage_articles(album_id):
    a = Album.query.get_or_404(album_id)
    if current_user != a.creator and not (current_user.is_administrator() or current_user.is_moderator()):
        abort(403)

    return render_template('auth/articles/album-articles-manage.html', album=a)


@auth.route('/post_manage/<int:post_id>', methods=['GET', 'POST'])
@login_required
@confirmed_required
def post_manage(post_id):
    p = Post.query.get_or_404(post_id)
    if current_user != p.author and not (current_user.is_administrator() or current_user.is_moderator()):
        abort(403)
    adopt_post_form = AdoptPostForm(prefix='adopt_post')
    if adopt_post_form.validate_on_submit():
        p.confirmed = True
        current_user.send_message(user=p.author, title=u'《%s》审核成功，已公开发表' % p.title,
                                  content=u'<p>尊敬的<strong>%s</strong></p><p><a href="%s">《%s》</a>经 %s 审核成功，已公开发表。</p>'
                                          % (p.author.username, url_for('main.post', post_id=p.id), p.title, current_user.username))
        return redirect(request.args.get('next') or url_for('auth.manage_articles', album_id=p.album.id))

    reject_post_form = RejectPostForm(prefix='reject_post')
    if reject_post_form.validate_on_submit():
        p.confirmed = False
        current_user.send_message(user=p.author, title=reject_post_form.title.data.strip(),
                                  content=u'<p>尊敬的<strong>%s</strong></p><p>很遗憾，您的<a href="%s">《%s》</a>经 %s 审核后，发表请求被驳回，原因如下：</p><p>%s</p>'
                                          % (p.author.username, url_for('main.post', post_id=p.id), p.title, current_user.username, reject_post_form.content.data.strip()))
        return redirect(request.args.get('next') or url_for('auth.manage_articles', album_id=p.album.id))

    return render_template('auth/articles/post-manage.html', post=p, adoptPostForm=adopt_post_form,
                           rejectPostForm=reject_post_form)


@auth.route('/my_albums', methods=['GET', 'POST'])
@login_required
@confirmed_required
def my_albums():
    page = request.args.get('page', 1, type=int)
    als = Album.query.filter_by(creator_id=current_user.id).order_by(Album.timestamp.desc()).paginate(page, error_out=False)

    return render_template('auth/albums/my-albums.html', albums=als)


@auth.route('/new_album', methods=['GET', 'POST'])
@login_required
@confirmed_required
def new_album():
    album_form = AlbumForm(prefix='album')
    if album_form.validate_on_submit():
        album = Album(title=album_form.title.data.strip(), picture_url=upload(f=album_form.picture.data, folder='album'),
                      percentage=float(album_form.percentage.data), introduction=album_form.introduction.data.strip(),
                      creator=current_user._get_current_object())
        db.session.add(album)
        return redirect(url_for('auth.my_albums'))

    return render_template('auth/albums/new-album.html', albumForm=album_form)


@auth.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
@confirmed_required
def edit_album(album_id):
    a = Album.query.get_or_404(album_id)
    if current_user != a.creator and not (current_user.is_administrator() or current_user.is_moderator()):
        abort(403)
    edit_album_form = EditAlbumForm(obj=a, prefix='edit_album')
    if edit_album_form.validate_on_submit():
        app = current_app._get_current_object()
        if edit_album_form.picture.data.filename is not u'':
            if a.picture_url and \
                    os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], 'album', a.picture_url)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'album', a.picture_url))
            a.picture_url = upload(f=edit_album_form.picture.data, folder='album')
        a.title = edit_album_form.title.data.strip()
        a.percentage = float(edit_album_form.percentage.data)
        a.introduction = edit_album_form.introduction.data.strip()
        a.confirmed = False
        return redirect(url_for('auth.my_albums'))

    return render_template('auth/albums/edit-album.html', album=a, editAlbumForm=edit_album_form)


@auth.route('/album_manage/<int:album_id>', methods=['GET', 'POST'])
@login_required
@confirmed_required
def album_manage(album_id):
    a = Album.query.get_or_404(album_id)
    if current_user != a.creator and not (current_user.is_administrator() or current_user.is_moderator()):
        abort(403)
    adopt_album_form = AdoptAlbumForm(prefix='adopt_album')
    if adopt_album_form.validate_on_submit():
        a.confirmed = True
        current_user.send_message(user=a.creator, title=u'《%s》审核成功，已公开发表' % a.title,
                                  content=u'<p>尊敬的<strong>%s</strong></p><p><a href="%s">《%s》</a>经 %s 审核成功，已公开发表。</p>'
                                          % (a.creator.username, url_for('main.album', album_id=a.id), a.title, current_user.username))
        return redirect(request.args.get('next') or url_for('auth.albums'))

    reject_album_form = RejectAlbumForm(prefix='reject_album')
    if reject_album_form.validate_on_submit():
        a.confirmed = False
        current_user.send_message(user=a.creator, title=reject_album_form.title.data.strip(),
                                  content=u'<p>尊敬的<strong>%s</strong></p><p>很遗憾，您的<a href="%s">《%s》</a>经 %s 审核后，发表请求被驳回，原因如下：</p><p>%s</p>'
                                          % (a.creator.username, url_for('main.album', album_id=a.id), a.title, current_user.username, reject_album_form.content.data.strip()))
        return redirect(request.args.get('next') or url_for('auth.albums'))

    return render_template('auth/albums/album-manage.html', album=a, adoptAlbumForm=adopt_album_form,
                           rejectAlbumForm=reject_album_form)


@auth.route('/my_messages', methods=['GET', 'POST'])
@login_required
@confirmed_required
def my_messages():
    delete_message_form = DeleteMessageForm(prefix='delete_message')
    if delete_message_form.validate_on_submit():
        m = Message.query.get(int(delete_message_form.message_id.data))
        if m:
            db.session.delete(m)
    all_read_message_form = AllReadMessageForm(prefix='all_read_message')
    if all_read_message_form.validate_on_submit():
        ms = Message.query.all()
        for m in ms:
            if not m.read:
                m.read = True
    message_form = MessageForm(prefix='message')
    if message_form.validate_on_submit():
        for m_id in request.form.getlist('message-checkbox'):
            if message_form.read.data:
                mess = Message.query.get(int(m_id))
                mess.read = True
            elif message_form.check_delete.data:
                msg = Message.query.get(int(m_id))
                db.session.delete(msg)

    message_form.checkbox.data = False
    message_form.check_delete.data = False
    message_form.read.data = False
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(receiver=current_user._get_current_object()).order_by(Message.timestamp.desc()).paginate(page, error_out=False)

    return render_template('auth/messages/my-messages.html', messages=messages, deleteMessageForm=delete_message_form,
                           allReadMessageForm=all_read_message_form, messageForm=message_form)


@auth.route('/my_collects', methods=['GET', 'POST'])
@login_required
@confirmed_required
def my_collects():
    page = request.args.get('page', 1, type=int)
    posts= Post.query.join(Collect, Collect.post_id==Post.id).filter(Collect.user_id==current_user.id)\
        .order_by(Collect.timestamp.desc()).paginate(page, error_out=False)

    return render_template('auth/collect/my-collects.html', posts=posts)


@auth.route('/my_subscribes', methods=['GET', 'POST'])
@login_required
@confirmed_required
def my_subscribes():
    page = request.args.get('page', 1, type=int)
    albums= Album.query.join(Subscribe, Subscribe.album_id==Album.id).filter(Subscribe.user_id==current_user.id)\
        .order_by(Subscribe.timestamp.desc()).paginate(page, error_out=False)

    return render_template('auth/subscribe/my-subscribes.html', albums=albums)


@auth.route('/to_read', methods=['GET', 'POST'])
@login_required
@confirmed_required
def to_read():

    return jsonify()


@auth.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
@confirmed_required
def users():
    search_user_form = SearchUserForm(prefix='search_user')
    page = request.args.get('page', 1, type=int)
    us = User.query.paginate(page, error_out=False)
    if search_user_form.validate_on_submit():
        from sqlalchemy import or_
        us = User.query.filter(or_(User.username.like('%' + '%s' % search_user_form.search.data.strip() + '%'),
                                   User.name.like('%' + '%s' % search_user_form.search.data.strip() + '%'),
                                   User.phone.like('%' + '%s' % search_user_form.search.data.strip() + '%')
                                   )).paginate(page, error_out=False)

    return render_template('auth/administrator/users.html', users=us, searchUserForm=search_user_form)


@auth.route('/user_admin_edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@confirmed_required
def user(user_id):
    user = User.query.get_or_404(user_id)
    edit_user_form = EditUserForm(prefix='edit_user', obj=user)
    edit_user_form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    if edit_user_form.validate_on_submit():
        app = current_app._get_current_object()
        user.name = edit_user_form.name.data.strip()
        user.phone = edit_user_form.phone.data.strip()
        user.about_me = edit_user_form.about_me.data.strip()
        user.role_id = edit_user_form.role_id.data

        if edit_user_form.disabled.data == u'True':
            user.disabled = True
        elif edit_user_form.disabled.data == u'False':
            user.disabled = False

        if user.picture_url and \
                os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], 'user', user.picture_url)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'user', user.picture_url))
        user.picture_url = upload(f=edit_user_form.picture.data, folder='user')
        return redirect(request.args.get('next') or url_for('auth.users'))

    return render_template('auth/administrator/user.html', editUserForm=edit_user_form, user=user)


@auth.route('/articles', methods=['GET', 'POST'])
@login_required
@admin_required
@confirmed_required
def articles():
    page = request.args.get('page', 1, type=int)
    ars = Post.query.order_by(Post.timestamp.desc()).paginate(page, error_out=False)
    off_post_form = OffPostForm(prefix='off_post')
    if off_post_form.validate_on_submit():
        p = Post.query.get_or_404(int(off_post_form.post_id.data.strip()))
        if not p.disabled:
            p.disabled = True

    return render_template('auth/administrator/articles.html', articles=ars, offPostForm=off_post_form)


@auth.route('/albums', methods=['GET', 'POST'])
@login_required
@admin_required
@confirmed_required
def albums():
    page = request.args.get('page', 1, type=int)
    als = Album.query.order_by(Album.timestamp.desc()).paginate(page, error_out=False)

    return render_template('auth/administrator/albums.html', albums=als)


@auth.route('/controller', methods=['GET', 'POST', 'OPTIONS'])
@login_required
@confirmed_required
def controller():
    """UEditor文件上传接口
    config 配置文件
    result 返回结果
    """
    app = current_app._get_current_object()
    mimetype = 'application/json'
    result = {}
    action = request.args.get('action')
    # 解析JSON格式的配置文件
    with open(os.path.join(app.static_folder, 'ueditor',
                           'config.json')) as fp:
        try:
            # 删除 `/**/` 之间的注释
            CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', fp.read()))
        except:
            CONFIG = {}
    if action == 'config':
        # 初始化时，返回配置文件给客户端
        result = CONFIG
    elif action in ('uploadimage', 'uploadfile', 'uploadvideo'):
        # 图片、文件、视频上传
        if action == 'uploadimage':
            fieldName = CONFIG.get('imageFieldName')
            config = {
                "pathFormat": CONFIG['imagePathFormat'],
                "maxSize": CONFIG['imageMaxSize'],
                "allowFiles": CONFIG['imageAllowFiles']
            }
        elif action == 'uploadvideo':
            fieldName = CONFIG.get('videoFieldName')
            config = {
                "pathFormat": CONFIG['videoPathFormat'],
                "maxSize": CONFIG['videoMaxSize'],
                "allowFiles": CONFIG['videoAllowFiles']
            }
        else:
            fieldName = CONFIG.get('fileFieldName')
            config = {
                "pathFormat": CONFIG['filePathFormat'],
                "maxSize": CONFIG['fileMaxSize'],
                "allowFiles": CONFIG['fileAllowFiles']
            }
        if fieldName in request.files:
            field = request.files[fieldName]
            uploader = Uploader(field, config)
            result = uploader.getFileInfo()
        else:
            result['state'] = '上传接口出错'
    elif action in ('uploadscrawl'):
        # 涂鸦上传
        fieldName = CONFIG.get('scrawlFieldName')
        config = {
            "pathFormat": CONFIG.get('scrawlPathFormat'),
            "maxSize": CONFIG.get('scrawlMaxSize'),
            "allowFiles": CONFIG.get('scrawlAllowFiles'),
            "oriName": "scrawl.png"
        }
        if fieldName in request.form:
            field = request.form[fieldName]
            uploader = Uploader(field, config, 'base64')
            result = uploader.getFileInfo()
        else:
            result['state'] = '上传接口出错'
    elif action in ('catchimage'):
        config = {
            "pathFormat": CONFIG['catcherPathFormat'],
            "maxSize": CONFIG['catcherMaxSize'],
            "allowFiles": CONFIG['catcherAllowFiles'],
            "oriName": "remote.png"
        }
        fieldName = CONFIG['catcherFieldName']
        source = []
        if fieldName in request.form:
            # 这里比较奇怪，远程抓图提交的表单名称不是这个
            source = []
        elif '%s[]' % fieldName in request.form:
            # 而是这个
            source = request.form.getlist('%s[]' % fieldName)
        _list = []
        for imgurl in source:
            uploader = Uploader(imgurl, config, 'remote')
            info = uploader.getFileInfo()
            _list.append({
                'state': info['state'],
                'url': info['url'],
                'original': info['original'],
                'source': imgurl,
            })
        result['state'] = 'SUCCESS' if len(_list) > 0 else 'ERROR'
        result['list'] = _list
    elif action in ('listimage'):
        config = {
            "pathFormat": CONFIG['imageManagerListPath'],
            "listSize": CONFIG['imageManagerListSize'],
            "allowFiles": CONFIG['imageManagerAllowFiles']
        }
        lists = List(config)
        result = lists.getFilesInfo()
    elif action in ('listfile'):
        config = {
            "pathFormat": CONFIG['fileManagerListPath'],
            "listSize": CONFIG['fileManagerListSize'],
            "allowFiles": CONFIG['fileManagerAllowFiles']
        }
        lists = List(config)
        result = lists.getFilesInfo()
    else:
        result['state'] = '请求地址出错'
    result = json.dumps(result)
    if 'callback' in request.args:
        callback = request.args.get('callback')
        if re.match(r'^[\w_]+$', callback):
            result = '%s(%s)' % (callback, result)
            mimetype = 'application/javascript'
        else:
            result = json.dumps({'state': 'callback参数不合法'})
    res = make_response(result)
    res.mimetype = mimetype
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,X_Requested_With'
    return res
