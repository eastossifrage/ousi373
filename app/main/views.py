# -*- coding:utf-8 -*-
__author__ = u'东方鹗'

from flask import render_template, request, redirect, url_for, flash, abort, g
from flask.ext.login import login_user, logout_user, login_required, current_user, current_app
from ..models import User, Album, Post
from .forms import SubscribeForm, CollectForm, SearchForm
from ..import db
from ..email import send_email
from .import main


@main.before_app_request
def before_request():
    search_form = SearchForm(prefix='search')
    page = request.args.get('page', 1, type=int)
    g.search_form = search_form
    if g.search_form.validate_on_submit() and g.search_form.value.data.strip() != '':
        from sqlalchemy import or_
        posts = Post.query.filter(or_(Post.body_html.like('%' + '%s' % g.search_form.value.data.strip() + '%'),
                                      Post.title.like('%' + '%s' % g.search_form.value.data.strip() + '%'),
                                      ),
                                  Post.confirmed==True, Post.disabled==False).order_by(Post.timestamp.desc())\
            .paginate(page, error_out=False)
        return render_template('main/search/posts.html', posts=posts)


@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    albums = Album.query.filter_by(confirmed=True, disabled=False).order_by(Album.timestamp.desc()).paginate(page, per_page=10, error_out=False)
    return render_template('main/index.html', albums=albums)

@main.route('/about')
def about():
    return render_template('main/about.html')



@main.route('/user/<username>')
def user(username):
    u = User.query.filter_by(username=username).first()
    if u is None:
        abort(404)
    my_albums = Album.query.filter_by(creator_id=u.id).all()
    my_posts = Post.query.filter_by(author_id=u.id).all()
    joined_albums = []
    for post in my_posts:
        if post.my_album.creator.id != u.id and post.my_album not in joined_albums:
            joined_albums.append(post.my_album)

    return render_template('main/user.html', user=u, my_albums=my_albums, joined_albums=joined_albums)


@main.route('/album/<int:album_id>', methods=['GET', 'POST'])
def album(album_id):
    a = Album.query.get_or_404(album_id)
    # if current_user != a.creator and not (current_user.is_administrator() or current_user.is_moderator()) and \
    #        (a.confirmed or not a.disabled):
    #    abort(403)
    subscribe_form = SubscribeForm(prefix='subscribe')
    if subscribe_form.validate_on_submit():
        if not current_user.is_authenticated():
            return redirect(request.args.get('next') or url_for('auth.login'))
        elif current_user.disabled:
            flash({'error': u'用户已被管理员注销！'})
            return redirect(request.args.get('next') or url_for('auth.login'))
        else:
            current_user.subscribe(album=a)
    post_confirmed_nums = Post.query.filter_by(album_id=a.id, confirmed=True, disabled=False).count()

    return render_template('main/album.html', album=a, subscribeForm=subscribe_form, post_confirmed_nums=post_confirmed_nums)


@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post(post_id):
    p = Post.query.get_or_404(post_id)
    collect_form = CollectForm(prefix='collect')
    if collect_form.validate_on_submit():
        if not current_user.is_authenticated():
            return redirect(request.args.get('next') or url_for('auth.login'))
        elif current_user.disabled:
            flash({'error': u'用户已被管理员注销！'})
            return redirect(request.args.get('next') or url_for('auth.login'))
        else:
            current_user.collect(post=p)

    posts = Post.query.filter_by(confirmed=True, disabled=False).all()
    pre_post = None
    next_post = None
    if p in posts:
        self_index = posts.index(p)
        if self_index - 1 >= 0:
            pre_post = posts[self_index - 1]
        if self_index + 1 < len(posts):
            next_post = posts[self_index + 1]
    return render_template('main/post.html', post=p, collectForm=collect_form, pre_post=pre_post, next_post=next_post)