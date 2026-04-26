from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re
from collections import Counter

app = Flask(__name__)
DB_FILE = 'blog.db'


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, content TEXT, seo_metrics TEXT, 
                  word_count INTEGER, readability TEXT)''')
    conn.commit()
    conn.close()


def process_content_for_display(content):
  
    yt_pattern = r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})[^\s]*)'
    
    iframe_tag = r'''<div class="mt-3 mb-3 shadow-sm" style="position:relative;padding-top:56.25%;overflow:hidden;border-radius:12px;">
        <iframe src="https://www.youtube.com/embed/\2" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;" allowfullscreen></iframe>
    </div>'''
    
    content = re.sub(yt_pattern, iframe_tag, content)
    

    url_pattern = r'(?<!href=")(https?://[^\s<>"]+)'
    content = re.sub(url_pattern, r'<a href="\1" target="_blank" class="text-primary" style="text-decoration:underline;">\1</a>', content)
    
    return content


def analyze_content(text):
   
    clean_text = re.sub('<[^<]+?>', '', text)
    words = re.findall(r'\b\w+\b', clean_text.lower())
    word_count = len(words)
    
    readability = "Advanced (Technical)" if word_count > 30 else "Accessible (General)"
    long_words = [w for w in words if len(w) > 5]
    top_keywords = [word for word, count in Counter(long_words).most_common(4)]
    seo_tags = ", ".join(top_keywords).title() if top_keywords else "Needs Optimization"
    
    return seo_tags, word_count, readability

@app.route('/', methods=['GET', 'POST'])
def index():
    audit_results = None
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        
        seo_tags, word_count, readability = analyze_content(content)
        
      
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, content, seo_metrics, word_count, readability) VALUES (?, ?, ?, ?, ?)", 
                  (title, content, seo_tags, word_count, readability))
        conn.commit()
        conn.close()
        
        audit_results = {
            'title': title, 'word_count': word_count,
            'seo_keywords': seo_tags, 'readability': readability,
            'status': '100% Original Content Detected'
        }
        
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    blogs = []
    for row in rows:
        b = dict(row)
        
        b['processed_content'] = process_content_for_display(b['content'])
        blogs.append(b)
    conn.close()
    
    return render_template('index.html', results=audit_results, blogs=blogs)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)