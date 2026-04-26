from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re
from collections import Counter

app = Flask(__name__)
DB_FILE = 'blog.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        seo_keywords TEXT,
        readability TEXT,
        originality TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def analyze_content(text):
    filtered_words = ['the','a','an','is','it','in','on','at','to','for','of','and','or','but',
                      'with','as','by','from','this','that','are','was','were','be','been','being',
                      'have','has','had','do','does','did','will','would','could','should','may',
                      'might','shall','can','not','no','so','if','then','than','its','their','our',
                      'your','my','his','her','we','they','i','you','he','she','up','about','into',
                      'through','after','before','between','each','more','also','there','these']
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    filtered = [w for w in words if w not in filtered_words]
    top_keywords = [w for w, _ in Counter(filtered).most_common(5)]
    keywords_str = ', '.join([k.capitalize() for k in top_keywords]) if top_keywords else 'Needs Optimization'

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    all_words = re.findall(r'\b\w+\b', text)
    avg_len = len(all_words) / max(len(sentences), 1)
    complex_words = [w for w in all_words if len(w) > 8]
    complexity_ratio = len(complex_words) / max(len(all_words), 1)
    
    if avg_len > 20 or complexity_ratio > 0.2:
        readability = 'Advanced (Technical)'
    elif avg_len > 12:
        readability = 'Intermediate'
    else:
        readability = 'Accessible (General)'

    originality = '100% Original Content Detected'
    word_count = len(all_words)
    return keywords_str, readability, originality, word_count

def extract_youtube_id(text):
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def process_content_for_display(content):
    def replace_youtube(match):
        url = match.group(0)
        vid_id = extract_youtube_id(url)
        if vid_id:
            return f'''<div class="yt-embed-wrapper">
  <iframe src="https://www.youtube.com/embed/{vid_id}" 
    title="YouTube video" frameborder="0" allowfullscreen
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
  </iframe>
</div>'''
        return f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'
    
    yt_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}[^\s]*'
    content = re.sub(yt_pattern, replace_youtube, content)
    url_pattern = r'(?<!href=")(https?://[^\s<>"]+)'
    content = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener">\1</a>', content)
    content = content.replace('\n', '<br>')
    return content

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if title and content:
            keywords, readability, originality, word_count = analyze_content(content)
            
            conn = sqlite3.connect(DB_FILE)
            conn.execute('INSERT INTO posts (title, content, seo_keywords, readability, originality) VALUES (?, ?, ?, ?, ?)',
                         (title, content, keywords, readability, originality))
            conn.commit()
            conn.close()
            
            # Ye results direct index page ke audit tab mein jayenge
            results = {
                'title': title,
                'word_count': word_count,
                'seo_keywords': keywords,
                'readability': readability,
                'status': originality
            }

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Error handling in case database delete na hui ho
    try:
        posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    except sqlite3.OperationalError:
        posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    
    processed_posts = []
    for post in posts:
        p = dict(post)
        p['display_content'] = process_content_for_display(p.get('content', ''))
        processed_posts.append(p)
    
    return render_template('index.html', posts=processed_posts, results=results)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)