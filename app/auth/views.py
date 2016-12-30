# -*- coding:utf-8 -*-

from flask import render_template, url_for, redirect, request, flash
from flask_login import login_user, login_required, logout_user, current_user

from .form import LoginForm, RegistrantionForm, ChangeEmailForm, ChangePasswordForm, PasswordResetForm, PasswordResetRequestForm
from ..email import send_email
from ..models import User
from . import auth
from .. import db


@auth.before_app_request
def before_request():
    """
    ..  note:: 处理程序中过滤未确认的账户

        同时满足以下 3 个条件时, `before_app_request` 处理程序会拦截请求。

        1.用户已登录( `current_user.is_authenticated()` 必须返回 `True` )。

        2.用户的账户还未确认。

        3.请求的端点(使用 request.endpoint 获取)不在认证蓝本中。
        访问认证路由要获取权限,因为这些路由的作用是让用户确认账户或执行其他账户管理操作。

    """
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    """
    用户未完成验证
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    ..  note:: 登录

        用户访问未授权的 URL 时会显示登录表单, Flask-Login会把原地址保存在查询字符串的 next 参数中。

        这个参数可从 request.args 字典中读取, 如果查询字符串中没有 next 参数,则重定向到首页。
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('用户名或密码有误！')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """
    退出账号
    """
    logout_user()
    flash("您已成功退出系统.")
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    ..  note:: 注册

        提交注册表单,通过验证后,系统就使用用户填写的信息在数据库中添加一个新用户。

    """
    form = RegistrantionForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        # 提交数据库之后才能赋予新用户 id 值,而确认令牌需要用到 id ,所以不能延后提交
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, "验证您的账户", 'auth/email/confirm',
                    user=user, token=token)
        flash('一封验证邮件已发送到您的邮箱，请登录邮箱进行验证！')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    """
    ..  note:: 确认用户的账户

        先检查已登录的用户是否已经确认过,如果确认过,则重定向到首页,
        因为很显然此时不用做什么操作。

        这样处理可以避免用户不小心多次点击确认令牌带来的额外工作。

        由于令牌确认完全在 User 模型中完成,所以视图函数只需调用 confirm() 方法即可,
        然后再根据确认结果显示不同的 Flash 消息。

        确认成功后, User 模型中 confirmed 属性的值会被修改并添加到会话中,
        请求处理完后,这两个操作被提交到数据库。
    """
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('您已验证该账号，感谢使用！')
    else:
        flash('验证链接已失效！')
    return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    """
    重新发送账户确认邮件
    """
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '验证您的账户',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的验证邮件已发送到您的邮箱，请登录邮箱进行验证！.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    修改密码
    """
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('您的密码已被修改！')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误！')
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    """
    重置密码请求
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '重置密码',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('一封验证重置密码请求的邮件已发送到您的邮箱，请登录邮箱进行验证！')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """
    重置密码
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('您的密码已修改！')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    """
    修改邮箱请求
    """
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, '验证您的邮箱地址',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('一封验证重置邮箱请求的邮件已发送到您的邮箱，请登录邮箱进行验证！')
            return redirect(url_for('main.index'))
        else:
            flash('邮箱或密码有误！')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    """
    修改邮箱
    """
    if current_user.change_email(token):
        flash('您的邮箱已修改！')
    else:
        flash('非法请求！')
    return redirect(url_for('main.index'))
