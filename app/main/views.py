# -*- coding:utf-8 -*-
from flask import abort,request, render_template, session,flash, redirect, url_for, current_app
from .. import db
from ..models import User, Movie, Record,Permission
from ..email import send_email
from . import main
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from .forms import EditMovieForm, AddMovieForm, SearchForm

@main.route('/', methods=['GET', 'POST'])
def index():
    """
    根地址
    """
    page = request.args.get('page',1,type=int)
    pagination = Movie.query.order_by(Movie.rating.desc()).paginate(
            page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    movies = pagination.items
    return render_template('index.html', movies=movies, pagination=pagination)

@login_required
@main.route('/user/<username>')
def user(username):
    """
    用户个人主页
    """
    max_borrow_number = current_app.config['MAX_BORROWED_NUMBER']
    user = User.query.filter_by(username=username).first()
    movies = user.borrowed_movies
    if user is None:
        abort(404)
    if user != current_user:
        abort(404)
    return render_template('user.html', user=user, movies=movies, max_borrow_number=max_borrow_number)

@login_required
@main.route('/movie/<id>')
def movie(id):
    """
    电影主页
    """
    movie = Movie.query.filter_by(id=id).first()
    if movie is None:
        abort(404)
    return render_template('movie.html', movie=movie)

@main.route('/borrow/<id>')
@login_required
@permission_required(Permission.BORROW)
def borrow(id):
    """
    借阅电影
    """
    movie = Movie.query.filter_by(id=id).first()
    if movie is None:
        flash('该影片不存在！')
        return redirect(url_for('.index'))
    if current_user.is_borrowing(movie):
        flash('您已经借阅《%s》！' % movie.title)
        return redirect(url_for('.movie', id=movie.id))
    current_user.borrow(movie, current_user)
    flash('恭喜你！成功借阅《%s》！' % movie.title)
    return redirect(url_for('.movie', id=movie.id))

@main.route('/return/<id>')
@login_required
@permission_required(Permission.RETURN)
def return_movie(id):
    """
    归还电影
    """
    movie = Movie.query.filter_by(id=id).first()
    if movie is None:
        flash('该影片不存在！')
        return redirect(url_for('.movie'))
    if not current_user.is_borrowing(movie):
        flash('您还没有借阅过该影片！')
        return redirect(url_for('.movie', id=id))
    current_user.return_movie(movie)
    flash('您已经归还《%s》！' % movie.title)
    return redirect(url_for('.movie', id=id))

@main.route('/edit-movie/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_movie(id):
    """
    修改电影信息
    """
    movie = Movie.query.get_or_404(id)
    form = EditMovieForm(movie=movie)
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.original_title = form.original_title.data
        movie.directors = form.directors.data
        movie.casts = form.casts.data
        movie.genres = form.genres.data
        movie.year = form.year.data
        movie.rating = form.rating.data
        movie.images = form.images.data
        movie.alt = form.alt.data
        movie.amount = form.amount.data
        movie.counts = form.counts.data
        db.session.add(movie)
        return redirect(url_for('.movie',id=movie.id))
    form.title.data = movie.title
    form.original_title.data = movie.original_title
    form.directors.data = movie.directors
    form.casts.data = movie.casts
    form.genres.data = movie.genres
    form.year.data = movie.year
    form.rating.data = movie.rating
    form.images.data = movie.images
    form.alt.data = movie.alt
    form.amount.data = movie.amount
    form.counts.data = movie.counts
    return render_template('edit-movie.html', form=form, movie=movie)

@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """
    搜索电影
    """
    form = SearchForm()
    if form.validate_on_submit():
        page = request.args.get('page',1,type=int)
        pagination = Movie.query.whoosh_search(form.search.data).paginate(
                page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                error_out=False)
        movies = pagination.items
        return render_template('search-result.html', movies=movies, pagination=pagination)
    return render_template('search.html', form=form)

@main.route('/add-movie', methods=['GET', 'POST'])
@login_required
@admin_required
def add_movie():
    """
    增加电影
    """
    form = AddMovieForm()
    if form.validate_on_submit():
        movie = Movie(title = form.title.data,
                    original_title = form.original_title.data,
                    directors = form.directors.data,
                    casts = form.casts.data,
                    genres = form.genres.data,
                    year = form.year.data,
                    rating = form.rating.data,
                    images = form.images.data,
                    alt = form.alt.data,
                    amount = form.amount.data
                 )
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('.movie',id=movie.id))
    return render_template('add-movie.html', form=form)

@main.route('/delete-movie/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_movie(id):
    """
    删除电影
    """
    movie = Movie.query.filter_by(id=id).first()
    if movie is None:
        flash('该影片不存在！')
        return redirect(url_for('.index'))
    if movie.is_borrowed:
        flash('该影片正在借阅中，无法删除！')
        return redirect(url_for('.index'))
    title = movie.title
    db.session.delete(movie)
    flash('您已经删除《%s》！' % title)
    return redirect(url_for('.index'))
