from flask import Flask, request, render_template, redirect, url_for, jsonify
import psycopg2
import os
import pika

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'appdb'),
        user=os.environ.get('DB_USER', 'appuser'),
        password=os.environ.get('DB_PASS', 'apppass')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

def send_task_to_queue(task):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'))
    )
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=str(task),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, description, due_date FROM tasks ORDER BY due_date ASC;')
    tasks = [
        {'id': row[0], 'title': row[1], 'description': row[2], 'due_date': row[3]}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, description, due_date FROM tasks ORDER BY due_date ASC;')
    tasks = [
        {'id': row[0], 'title': row[1], 'description': row[2], 'due_date': row[3]}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(tasks)

@app.route('/tasks', methods=['POST'])
def add_task():
    title = request.form.get('title')
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    if title:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO tasks (title, description, due_date) VALUES (%s, %s, %s) RETURNING id;',
            (title, description, due_date)
        )
        task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        # Send task info to RabbitMQ
        task = {'id': task_id, 'title': title, 'description': description, 'due_date': due_date}
        send_task_to_queue(task)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
