from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    """
    登录表单
    """
    email = StringField('邮箱', validators=[Required(), Length(1,64),Email()])
    password = PasswordField('密码', validators=[Required()])
    remember_me = BooleanField("记住我？")
    submit = SubmitField("登录")

class RegistrantionForm(FlaskForm):

    """
    ..  note:: 注册表单

        使用 WTForms 提供的 Regexp 验证函数,
        确保 username 字段只包含字母、数字和下划线。

        安全起见,密码要输入两次。此时要验证两个密码字段中的值是否一致,
        这种验证使用WTForms 提供的 EqualTo 验证函数实现。

    """
    email = StringField('邮箱', validators=[Required(), Length(1,64), Email()])
    username = StringField('用户名', validators=[Required(),
                    Length(1,32), Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0,
                                    '用户名必须只能包含字母、数字和下划线')])
    password = PasswordField('密码', validators=[Required(),
                    EqualTo('password2', message='密码必须一致！')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        """
        ..  note:: 为 email 字段定义了验证函数
            确保填写的值在数据库中没出现过。
            自定义的验证函数要想表示验证失败,
            可以抛出 ValidationError 异常,其参数就是错误消息。
        """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册！')

    def validate_username(self, field):
        """
        ..  note:: 为 username 字段定义了验证函数
            确保填写的值在数据库中没出现过。
            自定义的验证函数要想表示验证失败,
            可以抛出 ValidationError 异常,其参数就是错误消息。
        """
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用！')


class ChangePasswordForm(FlaskForm):
    """
    修改密码表单
    """
    old_password = PasswordField('旧密码', validators=[Required()])
    password = PasswordField('新密码', validators=[
        Required(), EqualTo('password2', message='密码必须一致！')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('修改密码')


class PasswordResetRequestForm(FlaskForm):
    """
    重置密码请求表单
    """
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('重置密码')


class PasswordResetForm(FlaskForm):
    """
    重置密码表单
    """
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('新密码', validators=[
        Required(), EqualTo('password2', message='密码必须一致！')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('请输入正确的邮箱！')


class ChangeEmailForm(FlaskForm):
    """
    修改邮箱表单
    """
    email = StringField('新邮箱', validators=[Required(), Length(1, 64),
                                                 Email()])
    password = PasswordField('密码', validators=[Required()])
    submit = SubmitField('修改邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被使用！')
