# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, validators
from wtforms.validators import Required, Length


class EditMovieForm(FlaskForm):
    title = StringField('原名', validators=[Length(0,64)])
    original_title = StringField('又名', validators=[Length(0,64)])
    directors = StringField('导演', validators=[Length(0,64)])
    casts = StringField('演员', validators=[Length(0,64)])
    genres = StringField('类型', validators=[Length(0,64)])
    year = IntegerField('年份')
    rating = FloatField('评分')
    images = StringField('封面', validators=[Length(0,128)])
    alt = StringField('豆瓣链接', validators=[Length(0,64)])
    amount = IntegerField('库存')
    counts = IntegerField('借阅次数')
    submit = SubmitField('提交')


class AddMovieForm(FlaskForm):
    title = StringField('原名', validators=[Length(0,64)])
    original_title = StringField('又名', validators=[Length(0,64)])
    directors = StringField('导演', validators=[Length(0,64)])
    casts = StringField('演员', validators=[Length(0,64)])
    genres = StringField('类型', validators=[Length(0,64)])
    year = IntegerField('年份')
    rating = FloatField('评分')
    images = StringField('封面', validators=[Length(0,128)])
    alt = StringField('豆瓣链接', validators=[Length(0,64)])
    amount = IntegerField('库存')
    submit = SubmitField('提交')


class SearchForm(FlaskForm):
    search = StringField('影片名', validators=[Length(0,64)])
    submit = SubmitField('提交')
