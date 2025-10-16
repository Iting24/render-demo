from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import inspect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='posts')
    content = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'author_id': self.author_id,
            'content': self.content,
        }


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def login_user(user):
    session.clear()
    session['user_id'] = user.id


def logout_user():
    session.clear()


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user():
            return jsonify({'error': 'authentication required'}), 401
        return f(*args, **kwargs)

    return wrapped


# create tables at import/startup to ensure compatibility with Flask 3.x
with app.app_context():
    # Ensure schema includes User and Post.author_id; for a simple dev/demo environment
    # we will recreate the database schema if it doesn't match the models.
    need_recreate = False
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'user' not in tables:
            need_recreate = True
        if 'post' in tables:
            cols = [c['name'] for c in inspector.get_columns('post')]
            if 'author_id' not in cols:
                need_recreate = True
    except Exception:
        need_recreate = True

    if need_recreate:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()


@app.route('/')
def index():
    # front-end fetches list via API; this page renders the container
    return render_template('index.html')


@app.route('/post/<int:post_id>')
def show_post(post_id):
    return render_template('post.html', post_id=post_id)


@app.route('/post/<int:post_id>/edit')
def edit_post_page(post_id):
    return render_template('edit_post.html', post_id=post_id)


@app.route('/new')
def new_post():
    return render_template('new_post.html')


# RESTful API endpoints for posts
@app.route('/api/posts', methods=['GET'])
def api_list_posts():
    posts = Post.query.order_by(Post.id.desc()).all()
    return jsonify([p.to_dict() for p in posts])


@app.route('/api/posts', methods=['POST'])
@login_required
def api_create_post():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    author = (data.get('author') or '').strip()
    content = (data.get('content') or '').strip()
    if not title or not author or not content:
        return jsonify({'error': 'title, author, content are required'}), 400

    user = current_user()
    post = Post(title=title, author=author, content=content, author_id=user.id)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def api_get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def api_update_post(post_id):
    post = Post.query.get_or_404(post_id)
    user = current_user()
    if not user or post.author_id != user.id:
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json() or {}
    title = data.get('title')
    author = data.get('author')
    content = data.get('content')
    if title is not None:
        post.title = title.strip()
    if author is not None:
        post.author = author.strip()
    if content is not None:
        post.content = content.strip()
    db.session.commit()
    return jsonify(post.to_dict())


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    user = current_user()
    if not user or post.author_id != user.id:
        return jsonify({'error': 'forbidden'}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({'result': 'deleted'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('username and password required', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('username already taken', 'danger')
            return render_template('register.html')
        u = User(username=username)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash('registered and logged in', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        u = User.query.filter_by(username=username).first()
        if not u or not u.check_password(password):
            flash('invalid credentials', 'danger')
            return render_template('login.html')
        login_user(u)
        flash('logged in', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('logged out', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # For development only; in production use a WSGI server
    app.run(debug=True)
