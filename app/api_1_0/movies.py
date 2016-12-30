from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import Movie, Permission
from . import api
from .decorators import permission_required
from .errors import forbidden


@api.route('/movies/')
def get_movies():
    count = current_app.config['FLASKY_JSONS_PER_PAGE']
    page = request.args.get('page', 1, type=int)
    pagination = Movie.query.paginate(
        page, per_page=count,
        error_out=False)
    movies = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_movies', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_movies', page=page+1, _external=True)
    return jsonify({
        'count': count,
        'start': (page - 1) * int(count),
        'total': pagination.total,
        'prev': prev,
        'next': next,
        'movies': [movie.to_json() for movie in movies]
    })

@api.route('/movies/<int:id>')
def get_movie(id):
    movie = Movie.query.get_or_404(id)
    return jsonify(movie.to_json())
