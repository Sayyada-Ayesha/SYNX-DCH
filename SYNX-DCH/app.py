from flask import Flask, render_template, request, redirect, url_for
import sqlite3, re
from collections import Counter

app = Flask(__name__)
DB_FILE = 'blog.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, content TEXT, seo_keywords TEXT,
        readability TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def analyze_content(text):
    # Basic Clean-up for AI Audit
    clean_text = re.sub('<[^<]+?>', '', text) # HTML tags hatana audit ke liye
    words = re.findall(r'\b\w{4,}\b', clean_text.lower())
    top_keywords = [w for w, _ in Counter(words).most_common(4)]
    
    # Readability Logic
    word_count = len(re.findall(r'\b\w+\b', clean_text))
    readability = "Advanced (Technical)" if word_count > 50 else "Accessible (General)"
    return ", ".join(top_keywords).title(), readability, word_count

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        keywords, readability, count = analyze_content(content)
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute('INSERT INTO posts (title, content, seo_keywords, readability) VALUES (?, ?, ?, ?)',
                     (title, content, keywords, readability))
        conn.commit()
        conn.close()
        results = {'title': title, 'keywords': keywords, 'readability': readability, 'count': count}

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', posts=posts, results=results)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)