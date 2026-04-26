from flask import Flask, render_template, request, redirect, url_for
import sqlite3, re
from collections import Counter

app = Flask(__name__)
DB_FILE = 'blog.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, content TEXT, seo_metrics TEXT, 
        word_count INTEGER, readability TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    audit_results = None
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        
        # Word Count & SEO Logic
        clean_text = re.sub('<[^<]+?>', '', content)
        words = re.findall(r'\b\w+\b', clean_text.lower())
        word_count = len(words)
        readability = "Advanced" if word_count > 30 else "Accessible"
        top_keywords = [w for w, _ in Counter([w for w in words if len(w)>5]).most_common(4)]
        seo_tags = ", ".join(top_keywords).title() if top_keywords else "N/A"
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("INSERT INTO posts (title, content, seo_metrics, word_count, readability) VALUES (?, ?, ?, ?, ?)", 
                     (title, content, seo_tags, word_count, readability))
        conn.commit()
        conn.close()
        audit_results = {'title': title, 'word_count': word_count, 'seo_keywords': seo_tags, 'readability': readability}
        
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    blogs = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', results=audit_results, blogs=blogs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)