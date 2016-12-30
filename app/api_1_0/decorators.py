from functools import wraps
from flask import g
from .errors import forbidden

def permission_required(permission):
    """
    ..  note:: 自定义装饰器

        用来防止未授权用户使用 POST 的 permission_required 修饰器
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('权限不足！')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
