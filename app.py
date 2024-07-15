from flask import Flask, render_template, request, redirect, url_for
import requests
import schedule
import time
import sqlite3
from threading import Thread

app = Flask(__name__)

ACCESS_TOKEN = ''
USER_ID = ''

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (id TEXT PRIMARY KEY, caption TEXT, media_url TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def get_latest_post():
    url = f'https://graph.instagram.com/{USER_ID}/media?fields=id,caption,media_url,timestamp&access_token={ACCESS_TOKEN}'
    response = requests.get(url)
    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        return data['data'][0]
    return None

def check_for_new_post():
    latest_post = get_latest_post()
    if latest_post:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id FROM posts WHERE id = ?', (latest_post['id'],))
        result = c.fetchone()
        if not result:
            c.execute('INSERT INTO posts (id, caption, media_url, timestamp) VALUES (?, ?, ?, ?)',
                      (latest_post['id'], latest_post.get('caption', ''), latest_post['media_url'], latest_post['timestamp']))
            conn.commit()
            send_notification(latest_post)
        conn.close()

def send_notification(post):
    post_url = post['media_url']
    caption = post.get('caption', 'No caption')
    timestamp = post['timestamp']
    print(f'New post detected at {timestamp}')
    print(f'Caption: {caption}')
    print(f'URL: {post_url}')
    # Add your email notification code here

def run_scheduler():
    schedule.every(5).minutes.do(check_for_new_post)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM posts ORDER BY timestamp DESC')
    posts = c.fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    init_db()
    Thread(target=run_scheduler).start()
    app.run(debug=True)
