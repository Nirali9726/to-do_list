from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── Models ──────────────────────────────────────────
class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    todos    = db.relationship('Todo', backref='owner', lazy=True)

class Category(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    todos   = db.relationship('Todo', backref='category', lazy=True)

class Todo(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    task        = db.Column(db.String(200), nullable=False)
    done        = db.Column(db.Boolean, default=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Auth routes ─────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ── Main / Search route ─────────────────────────────
@app.route('/')
@login_required
def index():
    search  = request.args.get('search', '')
    cat_filter = request.args.get('category', '')
    query = Todo.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(Todo.task.ilike(f'%{search}%'))
    if cat_filter:
        query = query.filter_by(category_id=cat_filter)
    todos      = query.all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', todos=todos, categories=categories,
                           search=search, cat_filter=cat_filter)

# ── Todo routes ─────────────────────────────────────
@app.route('/add', methods=['POST'])
@login_required
def add():
    task_text   = request.form.get('task')
    category_id = request.form.get('category_id') or None
    if task_text:
        todo = Todo(task=task_text, user_id=current_user.id, category_id=category_id)
        db.session.add(todo)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
@login_required
def complete(id):
    todo = Todo.query.get_or_404(id)
    todo.done = not todo.done
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

# ── Category routes ─────────────────────────────────
@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('category_name')
    if name:
        cat = Category(name=name, user_id=current_user.id)
        db.session.add(cat)
        db.session.commit()
    return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run(debug=True)
if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)