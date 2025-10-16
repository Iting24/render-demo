from app import app, db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    print('tables:', inspector.get_table_names())
    # show one row count for posts if table exists
    if 'post' in inspector.get_table_names():
        from app import Post
        res = db.session.query(Post).count()
        print('post rowcount:', res)
