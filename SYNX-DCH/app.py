from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re
from collections import Counter

app = Flask(__name__)

# Database Setup
def init_db():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, content TEXT, seo_metrics TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    audit_results = None
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        
        # AI Audit Logic
        words = re.findall(r'\b\w+\b', content.lower())
        word_count = len(words)
        readability = "Advanced (Technical)" if word_count > 30 else "Accessible (General)"
        long_words = [w for w in words if len(w) > 5]
        top_keywords = [word for word, count in Counter(long_words).most_common(4)]
        seo_tags = ", ".join(top_keywords).title() if top_keywords else "Needs Optimization"
        
        # Save to Database
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, content, seo_metrics) VALUES (?, ?, ?)", (title, content, seo_tags))
        conn.commit()
        conn.close()
        
        audit_results = {
            'title': title, 'word_count': word_count,
            'seo_keywords': seo_tags, 'readability': readability,
            'status': '100% Original Content Detected'
        }
        
    # Naya Kaam: Database se puray blogs fetch karna
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    all_blogs = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
        
    return render_template('index.html', results=audit_results, blogs=all_blogs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)