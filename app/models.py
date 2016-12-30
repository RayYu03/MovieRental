# -*- coding:utf-8 -*-
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin,current_user
from flask import current_app, request, url_for
from . import login_manager
from . import db
from datetime import datetime
from jieba.analyse import ChineseAnalyzer

DEFAULT_AVATAR_URL = "https://ws1.sinaimg.cn/large/647dc635jw1fb6f78kot1j20b40b4mx1.jpg"

class Permission:
    BORROW = 0x01
    RETURN = 0x02
    MODERATE_MOVIE = 0x04
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.BORROW |
                     Permission.RETURN, True),
            'Moderator': (Permission.BORROW |
                          Permission.RETURN |
                          Permission.MODERATE_MOVIE, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

class Record(db.Model):
    __tablename__ = 'records'
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)

class Movie(db.Model):
    __tablename__ = 'movies'
    __searchable__ = ['title', 'original_title']
    __analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, index=True)
    original_title = db.Column(db.String(64), unique=True, index=True)
    directors = db.Column(db.String(64))
    casts = db.Column(db.String(64))
    genres = db.Column(db.String(64))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float, default='0.0')
    images = db.Column(db.String(64))
    alt = db.Column(db.String(64))
    amount = db.Column(db.Integer,default=200)
    counts = db.Column(db.Integer,default=0)
    movie = db.relationship('Record', foreign_keys=[Record.movie_id],
                            backref=db.backref('movie',lazy='joined'),
                            lazy='dynamic',cascade='all, delete-orphan')

    def to_json(self):
        json_movie = {
            'title': self.title,
            'original_title': self.original_title,
            'directors': self.directors.split(' / '),
            'casts': self.casts.split(' / '),
            'genres': self.genres.split(' / '),
            'year': self.year,
            'rating': self.rating,
            'images': self.images,
            'api': url_for('api.get_movie', id=self.id, _external=True),
            'douban_alt': self.alt,
            'alt': url_for('main.movie', id=self.id, _external=True),
        }
        return json_movie

    def __repr__(self):
        return '<Movie %r>' % self.title

    def can(self):
        return self.amount > 0

    @property
    def is_borrowed(self):
        return self.movie.filter_by(movie_id=self.id).first() is not None

"""
    使用 flask_login 中的 UserMixin 代替自己实现的用户方法

    is_authenticated() 如果用户已经登录,必须返回 True ,否则返回 False
    is_active() 如果允许用户登录,必须返回 True ,否则返回 False 。
                如果要禁用账户,可以返回 False
    is_anonymous() 对普通用户必须返回 False
    get_id() 必须返回用户的唯一标识符,使用 Unicode 编码字符串
"""

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    amount = db.Column(db.Integer, default=7)
    avatar_url = db.Column(db.String(64), default=DEFAULT_AVATAR_URL)
    customer = db.relationship('Record', foreign_keys=[Record.customer_id],
                            backref=db.backref('customer',lazy='joined'),
                            lazy='dynamic',cascade='all, delete-orphan')

    def borrow(self, movie, user):
        if not self.is_borrowing(movie):
            if movie.can() and self.can_borrow():
                movie.amount -= 1
                movie.counts += 1
                self.amount -= 1
            r = Record(customer_id=user.id, movie_id=movie.id)
            db.session.add(r)

    def return_movie(self, movie):
        r = self.customer.filter_by(movie_id=movie.id).first()
        if r:
            movie.amount += 1
            self.amount += 1
            db.session.delete(r)

    def is_borrowing(self, movie):
        return self.customer.filter_by(movie_id=movie.id).first() is not None

    @property
    def borrowed_movies(self):
        r = self.customer.filter_by(customer_id=current_user.id).all()
        if r:
            movies = [Movie.query.filter_by(id=i.movie_id).first() for i in r]
            return movies
        else:
            return None

    def can_borrow(self):
        return self.amount > 0

    def __repr__(self):
        return '<User %r>' % self.username


    def generate_auth_token(self, expriation):
        s = Serializer(current_app.config['SECRET_KEY'],
                        expires_in=expriation)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    """
        计算密码散列值的函数通过名为 password 的只写属性实现。设定这个属性的值时,赋值
        方法会调用 Werkzeug 提供的 generate_password_hash() 函数,
        并把得到的结果赋值给 password_hash 字段。

        如果试图读取 password 属性的值,则会返回错误,原因很明显,
        因为生成散列值后就无法还原成原来的密码了。
        verify_password 方法接受一个参数(即密码)
        , 将其传给 Werkzeug 提供的 check_password_hash() 函数,
        和存储在 User 模型中的密码散列值进行比对。
        如果这个方法返回 True,就表明密码是正确的。
    """


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    """
        generate_confirmation_token() 方法生成一个令牌,有效期默认为一小时。

        confirm() 方法检验令牌,如果检验通过,则把新添加的 confirmed 属性设为 True 。

        除了检验令牌, confirm() 方法还检查令牌中的 id 是否和存储在
        current_user 中的已登录用户匹配。

        如此一来,即使恶意用户知道如何生成签名令牌,也无法确认别人的账户。
    """

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True


    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username

    def __init__(self, **kwagrs):
        super(User, self).__init__(**kwagrs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    """
        can() 方法在请求和赋予角色这两种权限之间进行位与操作。
        如果角色中包含请求的所有权限位,则返回 True ,
        表示允许用户执行此项操作。

        检查管理员权限的功能经常用到,
        因此使用单独的方法 is_administrator() 实现。
    """
    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)


"""
    加载用户的回调函数接收以 Unicode 字符串形式表示的用户标识符。
    如果能找到用户,这个函数必须返回用户对象;
    否则应该返回 None 。
"""
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser
