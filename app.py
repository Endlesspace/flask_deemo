from flask import Flask, render_template, request, flash, redirect, url_for, current_app, abort, jsonify
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField, TextAreaField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from config import DevConfig
import pymysql
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView

from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, AnonymousUserMixin, current_user, logout_user, \
    login_required
from datetime import datetime, timedelta, date
from flask_moment import Moment
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError, InternalError
from faker import Faker
import time

pymysql.install_as_MySQLdb()

app = Flask(__name__)
bootstrap = Bootstrap(app)
moment = Moment(app)

app.secret_key = 'Friday'
app.config.from_object(DevConfig)
db = SQLAlchemy(app)
admin = Admin(app, name='平台管理', template_mode='bootstrap3')
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
migrate = Migrate(app, db)
# 自动加载html模版
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Model


class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.role.name == '管理员'

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        print("没有权限")
        return redirect(url_for('login', next=request.url))


# 用户资料编辑


class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    about_me = TextAreaField('简介')
    submit = SubmitField('提交')


class Loginform(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('保持登录')
    submit = SubmitField('登录')


class Registform(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='两次密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    role = RadioField('选择身份', validators=[DataRequired()], choices=[(1, '普通用户'), (2, '心理咨询师')], default=1, coerce=int)
    submit = SubmitField('提交')


# 留言表格


class PostForm(FlaskForm):
    body = TextAreaField("我想留言", validators=[DataRequired()])
    submit = SubmitField('提交')


# 编辑自己留言的表格


class ChangeForm(FlaskForm):
    body = TextAreaField("更改留言", validators=[DataRequired()])
    submit = SubmitField('提交并返回')


# 从管理员页面退出


class Myexit(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def admin_index(self):
        return redirect(url_for('top'))


# 咨询文章


class Respost(db.Model):
    __tablename__ = 'resposts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    author = db.Column(db.String(20))
    category = db.Column(db.Integer)

    @staticmethod
    def article(count=100):
        fake = Faker("zh_CN")
        for i in range(count):
            r = Respost(title=fake.text(), body=fake.text(), timestamp=fake.date_time(), author=fake.name(),
                        category=fake.random_int())

            db.session.add(r)
            try:
                db.session.commit()
                i += 1
            except IntegrityError:
                db.session.commit()


# 心理视频

class Video(db.Model):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    instruction = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    author = db.Column(db.String(255))
    address = db.Column(db.String(255))


# 留言文章


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 关联评论
    comments = db.relationship('Comment', backref='post', lazy='dynamic')


# 权限


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


# 评论类


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))


# 预约单类
class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(15))
    order_time = db.Column(db.DateTime, index=True, default=datetime.now)
    order_from = db.Column(db.Integer)
    order_to = db.Column(db.Integer)
    state = db.Column(db.Integer)  # 未处理（0）/已取消（1）/已结束（2）
    appointment_time = db.Column(db.DateTime, index=True, default=datetime.now() + timedelta(hours=1))


# 留言评论


class CommentForm(FlaskForm):
    body = StringField('输入您的评论', validators=[DataRequired()])
    submit = SubmitField('提交')


# 角色


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    permissions = db.Column(db.Integer)
    # 关联用户
    users = db.relationship('User', backref='role')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            '普通用户': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            '咨询师': [Permission.FOLLOW, Permission.COMMENT,
                    Permission.WRITE, Permission.MODERATE],
            '管理员': [Permission.FOLLOW, Permission.COMMENT,
                    Permission.WRITE, Permission.MODERATE,
                    Permission.ADMIN],
        }
        # default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            # role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm


# 用户


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    about_me = db.Column(db.Text())
    name = db.Column(db.String(64))
    # 关联角色
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 关联评论
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def verify_password(self, string):
        if self.password == string:
            return True
        else:
            return False

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def __repr__(self):
        return "<User '{}'>".format(self.username)


# 匿名用户
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


admin.add_view(AdminModelView(User, db.session))
admin.add_view(AdminModelView(Role, db.session))
admin.add_view(AdminModelView(Post, db.session))
admin.add_view(AdminModelView(Comment, db.session))
admin.add_view(Myexit(name='exit'))


# 路由


# 资讯


@app.route('/res')
def res():
    page = request.args.get('page', 1, type=int)
    pagination = Respost.query.order_by(Respost.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_RESPOSTS_PER_PAGE'],
        error_out=False)
    news = pagination.items
    page2 = request.args.get('page', 1, type=int)
    pagination2 = Video.query.order_by(Video.timestamp.desc()).paginate(
        page2, per_page=current_app.config['FLASKY_RESPOSTS_PER_PAGE'],
        error_out=False)
    videos = pagination2.items
    return render_template('index.html', news=news, pagination=pagination, videos=videos, pagination2=pagination2)


# 新闻详情


@app.route('/details/news/<id>')
def news(id):
    respost = Respost.query.filter_by(id=id).first_or_404()
    return render_template('details.html', respost=respost, type='n')


# 视频


@app.route('/details/video/<id>')
def video(id):
    videos = Video.query.filter_by(id=id).first_or_404()
    return render_template('details.html', videos=videos, type='v')


# 心理咨询

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    return render_template('chat.html')


# 查看当天已预约，前面还有多少人
@app.route('/queue', methods=['GET', 'POST'])
@login_required
def queue():
    doctor = request.json.get("doctor")
    count = None
    if current_user.role_id == 1:
        patient = current_user.id
        sql = "SELECT count(*) AS count FROM `order` WHERE TO_DAYS(appointment_time)=TO_DAYS(NOW()) AND (SELECT id FROM users WHERE username='{}') AND state=0 AND order_time< ( SELECT order_time FROM `order` WHERE TO_DAYS(appointment_time)=TO_DAYS(NOW()) AND ( SELECT id FROM users WHERE username='{}') AND state=0 AND order_from={})".format(
            doctor, doctor, patient)
        try:
            count = db.session.execute(sql).first().count
        except InternalError as e:
            print(e)
    return jsonify({
        "count": count
    })


@app.route('/end', methods=['GET', 'POST'])
@login_required
def end():
    order_id = request.json.get("order_id")
    this_order = Order.query.filter(Order.order_id == order_id).first()
    this_order.state = 2
    try:
        db.session.add(this_order)
        db.session.commit()
    except IntegrityError as e:
        print(e)
    return "hhh"


# 编辑留言


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMIN):
        abort(403)
    form = ChangeForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('留言已更新')
        return redirect(url_for('.top'))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


# 资料编辑


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('您的资料已更新')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


# 个人资料


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(author=current_user._get_current_object()).order_by(
        Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


# 注销


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录')
    return redirect(url_for('top'))


# 主界面
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


# 留言板


@app.route('/top', methods=['GET', 'POST'])
def top():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.top'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('top.html', form=form, posts=posts, Permission=Permission, pagination=pagination)


# 博客文章


@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('评论已提交')
        return redirect(url_for('.post', id=post.id))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
               current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, Permission=Permission, comments=comments,
                           pagination=pagination)


# 登录界面


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Loginform()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('top'))
        flash('无效的用户名或密码')
    return render_template('login.html', form=form)


# 注册


@app.route('/regist', methods=['GET', 'POST'])
def regist():
    username = None
    password = None
    password2 = None
    regist_form = Registform()
    if regist_form.validate_on_submit():
        username = regist_form.username.data
        password = regist_form.password.data
        role_id = regist_form.role.data

        # 清空表单1
        regist_form.username.data = ''
        regist_form.password.data = ''
        regist_form.password2.data = ''
        user = User(username=username, password=password, role_id=role_id)
        if User.query.filter_by(username=username).first() is None:
            db.session.add(user)
            db.session.commit()
            flash('注册成功')
            return redirect(url_for('login'))
        else:
            flash('已存在该用户')
            redirect(url_for('regist'))

    return render_template('regist.html', regist_form=regist_form)


# 预约界面
@app.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    if current_user.role_id == 1:
        page = request.args.get('page', 1, type=int)
        pagination = User.query.filter(User.role_id == 2).paginate(
            page, per_page=current_app.config['FLASKY_DOCTOR_PER_PAGE'],
            error_out=False)
        doctors = pagination.items
        return render_template('order.html', doctors=doctors, pagination=pagination)
    elif current_user.role_id == 2:
        # 查找未处理的预约
        page = request.args.get('page', 1, type=int)
        pagination = db.session.query(User, Order).filter(and_(User.id == Order.order_from),
                                                          Order.order_to == current_user.id, Order.state == 0).order_by(
            Order.appointment_time, Order.order_time).paginate(
            page, per_page=current_app.config[
                'FLASKY_POSTS_PER_PAGE'],
            error_out=False)
        items = pagination.items
        option = '待处理列表'
        # 查询待处理人数
        sql = "SELECT COUNT(order_id) as count from users inner join `order` where users.id =`order`.order_from and `order`.order_to = {} and `order`.state =0".format(
            current_user.id)
        count = db.session.execute(sql).first().count
        return render_template("waitinglist.html", items=items, pagination=pagination, option=option, count=count)
    else:
        return "无法预约"


# 显示全部的预约
@app.route('/order/all', methods=['GET', 'POST'])
@login_required
def allorder():
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(User, Order).filter(and_(User.id == Order.order_from),
                                                      Order.order_to == current_user.id).order_by(
        Order.order_time).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    items = pagination.items
    option = '全部预约（点击返回）'
    return render_template("waitinglist.html", items=items, pagination=pagination, option=option)


# 从咨询师列表添加预约，暂时使用路由来实现
@app.route('/order/', methods=['GET', 'POST'])
def create():
    from_p = request.json.get("from_p")
    to_d = request.json.get("to_d")
    app_time = request.json.get("time")
    # 将日期的从string转为date格式
    app_time = date(*map(int, app_time.split('-')))
    # 判断是否有当前医生未处理的预约
    check_pre = db.session.query(Order).filter(and_(Order.order_from == from_p), Order.order_to == to_d,
                                               Order.state == 0)
    # 这个方法与.one_or_none()的效果一样。
    # 如果查询到很多结果，抛出sqlalchemy.orm.exc.MultipleResultsFound异常。
    check = db.session.query(check_pre.exists()).scalar()
    if not check:
        order = Order(order_from=from_p, order_to=to_d, state=0, appointment_time=app_time,
                      order_id=time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))
        db.session.add(order)
        db.session.commit()
        return jsonify({"ok": True})
    else:
        # 响应返回json
        return jsonify({"ok": False})

    return redirect((url_for('.order')))


# 我的预约界面/咨询师查看当前预约列表
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if current_user.role_id == 1:
        page = request.args.get('page', 1, type=int)
        pagination = db.session.query(User, Order).filter(and_(User.id == Order.order_to),
                                                          Order.order_from == current_user.id).order_by(
            Order.order_time.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
        orders = pagination.items

    else:
        flash("无预约权限")
        return redirect((url_for('.order')))

    return render_template("appointments.html", orders=orders, pagination=pagination)


# 取消预约
@app.route('/cancel/<string:order_id>', methods=['GET', 'POST'])
@login_required
def cancel(order_id):
    # db.session.add()内部必须为对象，所以item后面需要加.first()
    item = Order.query.filter_by(order_id=order_id).first()
    item.state = 1
    db.session.add(item)
    db.session.commit()
    flash("预约已取消")
    return redirect("/appointments")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
