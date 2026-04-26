from flask import Flask, render_template, request, redirect, url_for
import sqlite3, re
from collections import Counter

app = Flask(__name__)
DB_FILE = 'blog.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, content TEXT, seo_metrics TEXT, 
                  word_count INTEGER, readability TEXT, 
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def process_youtube(content):
    # Asli "Preview" Logic: YouTube link ko player mein badalna
    yt_pattern = r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})[^\s]*)'
    iframe = r'''<div class="mt-3 mb-3 shadow" style="position:relative;padding-top:56.25%;overflow:hidden;border-radius:12px;">
        <iframe src="https://www.youtube.com/embed/\2" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;" allowfullscreen></iframe>
    </div>'''
    return re.sub(yt_pattern, iframe, content)

@app.route('/', methods=['GET', 'POST'])
def index():
    audit_results = None
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        
        words = re.findall(r'\b\w+\b', re.sub('<[^<]+?>', '', content).lower())
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
    rows = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    all_posts = []
    for row in rows:
        p = dict(row)
        p['display_content'] = process_youtube(p['content'])
        all_posts.append(p)
    conn.close()
    return render_template('index.html', results=audit_results, posts=all_posts)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)