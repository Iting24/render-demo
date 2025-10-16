from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Post {self.id} {self.title}>"


@app.before_first_request
def create_tables():
    db.create_all()


@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/post/<int:post_id>')
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)


@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()

        if not title or not author or not content:
            flash('請填寫標題、作者與內容', 'danger')
            return render_template('new_post.html', title=title, author=author, content=content)

        post = Post(title=title, author=author, content=content)
        db.session.add(post)
        db.session.commit()
        flash('文章已建立', 'success')
        return redirect(url_for('show_post', post_id=post.id))

    return render_template('new_post.html')


if __name__ == '__main__':
    # For development only; in production use a WSGI server
    app.run(debug=True)
