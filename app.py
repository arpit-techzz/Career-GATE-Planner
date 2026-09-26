from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- DATABASE MODELS ----------

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

@app.route('/dashboard')
def dashboard():
    subjects = Subject.query.all()
    tasks = Task.query.order_by(Task.due_date).limit(10).all()
    goals = CareerGoal.query.all()

    total_topics = sum(s.total_topics for s in subjects)
    completed_topics = sum(s.completed_topics for s in subjects)
    overall_progress = int((completed_topics / total_topics) * 100) if total_topics else 0

    pending = Task.query.filter_by(status='Pending').count()
    completed = Task.query.filter_by(status='Completed').count()

    return render_template(
        'dashboard.html',
        subjects=subjects,
        tasks=tasks,
        goals=goals,
        overall_progress=overall_progress,
        pending=pending,
        completed=completed
    )

@app.route('/syllabus')
def syllabus():
    subjects = Subject.query.all()
    return render_template('syllabus.html', subjects=subjects)

@app.route('/tasks')
def tasks_page():
    tasks = Task.query.order_by(Task.due_date).all()
    subjects = Subject.query.all()
    return render_template('tasks.html', tasks=tasks, subjects=subjects)

@app.route('/career')
def career():
    goals = CareerGoal.query.all()
    return render_template('career.html', goals=goals)

# ---------- API ENDPOINTS ----------

# Subjects
@app.route('/api/subject', methods=['POST'])
def add_subject():
    data = request.json
    s = Subject(
        name=data['name'],
        branch=data.get('branch', 'CSE'),
        total_topics=int(data.get('total_topics', 0)),
        completed_topics=int(data.get('completed_topics', 0)),
        priority=data.get('priority', 'Medium')
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': s.id})

@app.route('/api/subject/<int:sid>', methods=['PUT'])
def update_subject(sid):
    s = Subject.query.get_or_404(sid)
    data = request.json
    if 'completed_topics' in data:
        s.completed_topics = min(int(data['completed_topics']), s.total_topics)
    if 'name' in data:
        s.name = data['name']
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
    data = request.json
    due = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None
    t = Task(
        title=data['title'],
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
    data = request.json
    if 'status' in data:
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
    data = request.json
    td = datetime.strptime(data['target_date'], '%Y-%m-%d').date() if data.get('target_date') else None
    g = CareerGoal(
        title=data['title'],
        category=data.get('category'),
        target_date=td,
        description=data.get('description', ''),
        progress=int(data.get('progress', 0))
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': g.id})

@app.route('/api/goal/<int:gid>', methods=['PUT'])
def update_goal(gid):
    g = CareerGoal.query.get_or_404(gid)
    data = request.json
    if 'progress' in data:
        g.progress = max(0, min(100, int(data['progress'])))
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, host='127.0.0.1', port=8000)
    