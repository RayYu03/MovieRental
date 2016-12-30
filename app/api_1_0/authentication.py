from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    """
    ..  note:: 支持令牌的改进验证回调

        第一个认证参数可以是电子邮件地址或认证令牌。

        如果这个参数为空,那就假定是匿名用户。

        如果密码为空,那就假定 email_or_token 参数提供的是令牌,按照令牌的方式进行认证。

        如果两个参数都不为空,假定使用常规的邮件地址和密码进行认证。

        在这种实现方式中,基于令牌的认证是可选的,由客户端决定是否使用。

        为了让视图函数能区分这两种认证方法, 添加了 g.token_used 变量。

    """
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token) #???
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    """
    认证错误
    """
    return unauthorized('证书错误！')


@api.before_request
@auth.login_required
def before_request():
    """
    防止匿名用户和未认证用户非法访问
    """
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('未验证的账户！')


@api.route('/token')
def get_token():
    """
    生成认证令牌
    """
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
