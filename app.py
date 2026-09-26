from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from werkzeug.security import generate_password_hash, check_password_hash

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=ROOT_DIR, static_folder=ROOT_DIR,
            static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(ROOT_DIR, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- DATABASE MODELS ----------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    branch = db.Column(db.String(50), default='CSE')  # CSE, ECE, ME, etc.
    total_topics = db.Column(db.Integer, default=0)
    completed_topics = db.Column(db.Integer, default=0)
    priority = db.Column(db.String(20), default='Medium')  # High/Medium/Low

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(120))
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending/Completed
    priority = db.Column(db.String(20), default='Medium')

class CareerGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80))  # PSU, M.Tech, Job, Higher Studies
    target_date = db.Column(db.Date)
    description = db.Column(db.Text)
    progress = db.Column(db.Integer, default=0)  # 0-100

# ---------- ROUTES ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not name or not email or not password:
        return render_template('signup.html', error='All fields are required.',
                               name=name, email=email), 400
    if '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
        return render_template('signup.html', error='Enter a valid email address.',
                               name=name, email=email), 400
    if len(password) < 8:
        return render_template('signup.html', error='Password must be at least 8 characters.',
                               name=name, email=email), 400
    if password != confirm_password:
        return render_template('signup.html', error='Passwords do not match.',
                               name=name, email=email), 400
    if User.query.filter_by(email=email).first():
        return render_template('signup.html', error='An account with that email already exists.',
                               name=name, email=email), 409

    user = User(name=name, email=email,
                password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    session.clear()
    session['user_id'] = user.id
    return redirect(url_for('dashboard'))

@app.route('/signin', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template('signin.html',
                               error='Email or password is incorrect.',
                               email=email), 401
    session.clear()
    session['user_id'] = user.id
    return redirect(url_for('dashboard'))

@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    subjects = Subject.query.all()
    tasks = Task.query.order_by(Task.due_date.is_(None), Task.due_date).limit(10).all()
    goals = CareerGoal.query.all()

    total_topics = sum(s.total_topics for s in subjects)
    completed_topics = sum(s.completed_topics for s in subjects)
    overall_progress = int((completed_topics / total_topics) * 100) if total_topics else 0

    pending = Task.query.filter_by(status='Pending').count()
    completed = Task.query.filter_by(status='Completed').count()
    overdue = Task.query.filter(
        Task.status == 'Pending',
        Task.due_date.isnot(None),
        Task.due_date < date.today()
    ).count()

    return render_template(
        'dashboard.html',
        subjects=subjects,
        tasks=tasks,
        goals=goals,
        overall_progress=overall_progress,
        pending=pending,
        completed=completed,
        overdue=overdue,
        today=date.today()
    )

@app.route('/syllabus')
def syllabus():
    subjects = Subject.query.all()
    return render_template('syllabus.html', subjects=subjects)

@app.route('/tasks')
def tasks_page():
    tasks = Task.query.order_by(Task.due_date.is_(None), Task.due_date).all()
    subjects = Subject.query.all()
    return render_template('tasks.html', tasks=tasks, subjects=subjects)

@app.route('/career')
def career():
    goals = CareerGoal.query.all()
    return render_template('career.html', goals=goals)

# ---------- API ENDPOINTS ----------

def json_error(message, status=400):
    return jsonify({'status': 'error', 'message': message}), status

def request_data():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}

def parse_date(value, field_name):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must use YYYY-MM-DD format')

# Subjects
@app.route('/api/subject', methods=['POST'])
def add_subject():
    data = request_data()
    if not str(data.get('name', '')).strip():
        return json_error('Subject name is required')
    try:
        total_topics = int(data.get('total_topics', 0))
        completed_topics = int(data.get('completed_topics', 0))
    except (TypeError, ValueError):
        return json_error('Topic counts must be whole numbers')
    if total_topics < 1 or completed_topics < 0:
        return json_error('Total topics must be at least 1 and completed topics cannot be negative')
    if completed_topics > total_topics:
        return json_error('Completed topics cannot exceed total topics')
    s = Subject(
        name=str(data['name']).strip(),
        branch=data.get('branch', 'CSE'),
        total_topics=total_topics,
        completed_topics=completed_topics,
        priority=data.get('priority', 'Medium')
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': s.id})

@app.route('/api/subject/<int:sid>', methods=['PUT'])
def update_subject(sid):
    s = Subject.query.get_or_404(sid)
    data = request_data()
    if 'completed_topics' in data:
        try:
            completed_topics = int(data['completed_topics'])
        except (TypeError, ValueError):
            return json_error('Completed topics must be a whole number')
        s.completed_topics = max(0, min(completed_topics, s.total_topics))
    if 'name' in data:
        if not str(data['name']).strip():
            return json_error('Subject name cannot be empty')
        s.name = str(data['name']).strip()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/subject/<int:sid>', methods=['DELETE'])
def delete_subject(sid):
    s = Subject.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'status': 'ok'})

# Tasks
@app.route('/api/task', methods=['POST'])
def add_task():
    data = request_data()
    if not str(data.get('title', '')).strip():
        return json_error('Task title is required')
    try:
        due = parse_date(data.get('due_date'), 'Due date')
    except ValueError as error:
        return json_error(str(error))
    t = Task(
        title=str(data['title']).strip(),
        subject=data.get('subject'),
        due_date=due,
        priority=data.get('priority', 'Medium')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': t.id})

@app.route('/api/task/<int:tid>', methods=['PUT'])
def update_task(tid):
    t = Task.query.get_or_404(tid)
    data = request_data()
    if 'status' in data:
        if data['status'] not in ('Pending', 'Completed'):
            return json_error('Status must be Pending or Completed')
        t.status = data['status']
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/task/<int:tid>', methods=['DELETE'])
def delete_task(tid):
    t = Task.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'status': 'ok'})

# Career Goals
@app.route('/api/goal', methods=['POST'])
def add_goal():
    data = request_data()
    if not str(data.get('title', '')).strip():
        return json_error('Goal title is required')
    try:
        td = parse_date(data.get('target_date'), 'Target date')
        progress = max(0, min(100, int(data.get('progress', 0))))
    except (ValueError, TypeError):
        return json_error('Progress must be a number and target date must use YYYY-MM-DD format')
    g = CareerGoal(
        title=str(data['title']).strip(),
        category=data.get('category'),
        target_date=td,
        description=data.get('description', ''),
        progress=progress
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': g.id})

@app.route('/api/goal/<int:gid>', methods=['PUT'])
def update_goal(gid):
    g = CareerGoal.query.get_or_404(gid)
    data = request_data()
    if 'progress' in data:
        try:
            g.progress = max(0, min(100, int(data['progress'])))
        except (TypeError, ValueError):
            return json_error('Progress must be a whole number')
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/goal/<int:gid>', methods=['DELETE'])
def delete_goal(gid):
    g = CareerGoal.query.get_or_404(gid)
    db.session.delete(g)
    db.session.commit()
    return jsonify({'status': 'ok'})

# ---------- SEED DATA (first run) ----------
def seed_data():
    if Subject.query.count() == 0:
        default_subjects = [
            ('Engineering Mathematics', 'CSE', 20, 4, 'High'),
            ('Data Structures', 'CSE', 15, 3, 'High'),
            ('Algorithms', 'CSE', 12, 2, 'High'),
            ('Operating Systems', 'CSE', 10, 1, 'Medium'),
            ('DBMS', 'CSE', 8, 2, 'Medium'),
            ('Computer Networks', 'CSE', 9, 0, 'Medium'),
            ('Theory of Computation', 'CSE', 10, 0, 'Low'),
            ('Compiler Design', 'CSE', 8, 0, 'Low'),
        ]
        for n, b, t, c, p in default_subjects:
            db.session.add(Subject(name=n, branch=b, total_topics=t,
                                   completed_topics=c, priority=p))
        db.session.commit()

@app.before_request
def initialize_database():
    db.create_all()
    seed_data()
    g.user = None
    user_id = session.get('user_id')
    if user_id:
        g.user = db.session.get(User, user_id)
        if g.user is None:
            session.clear()

    public_endpoints = {'index', 'signup', 'signin', 'static'}
    if request.endpoint not in public_endpoints and g.user is None:
        if request.path.startswith('/api/'):
            return json_error('Authentication required', 401)
        return redirect('/signin?next=' + request.path)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8000)
    