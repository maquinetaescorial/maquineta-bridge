import os
import json
from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import requests

app = Flask(__name__)
DATABASE = 'messages.db'
DEEPSEEK_API_KEY = "sk-d53a42e144334d1bb670ef5a5c4ef7c6"  # <-- POSA LA TEVA CLAU AQUÍ
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  author TEXT,
                  text TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/chat/receive', methods=['POST'])
def receive_message():
    data = request.json
    author = data.get('author')
    text = data.get('text')
    if not author or not text:
        return jsonify({'error': 'missing fields'}), 400
    timestamp = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (timestamp, author, text) VALUES (?, ?, ?)",
              (timestamp, author, text))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/chat/messages', methods=['GET'])
def get_messages():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT timestamp, author, text FROM messages ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    messages = [{"timestamp": r[0], "author": r[1], "text": r[2]} for r in rows]
    return jsonify(messages[::-1])

def deepseek_respond(text):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": text}],
        "temperature": 0.7
    }
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            return f"[Error DeepSeek: {r.status_code}]"
    except Exception as e:
        return f"[Error de connexió: {e}]"

@app.route('/deepseek/ask', methods=['POST'])
def ask_deepseek():
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': 'missing text'}), 400
    resposta = deepseek_respond(text)
    return jsonify({'response': resposta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
