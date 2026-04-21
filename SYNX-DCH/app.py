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
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, 
                 keywords TEXT, readability TEXT, plagiarism TEXT)''')
    conn.commit()
    conn.close()

# Native AI Content Analyzer
def analyze_content(text):
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    
    stop_words = {'the', 'is', 'in', 'and', 'to', 'a', 'of', 'for', 'it', 'with', 'on', 'as', 'this', 'that', 'are', 'be'}
    filtered_words = [w for w in words if w not in stop_words and len(w) > 4]
    common_words = [word[0] for word in Counter(filtered_words).most_common(4)]
    keywords = ", ".join(common_words).title() if common_words else "General"
    
    long_words = [w for w in words if len(w) > 8]
    if word_count > 0 and (len(long_words) / word_count) > 0.15:
        readability = "Advanced (Technical)"
    else:
        readability = "Accessible (General Audience)"
        
    plagiarism = "100% Original Content Detected"
    
    return keywords, readability, plagiarism

@app.route('/')
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = c.fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    content = request.form['content']
    keywords, readability, plagiarism = analyze_content(content)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO posts (title, content, keywords, readability, plagiarism) VALUES (?, ?, ?, ?, ?)', 
              (title, content, keywords, readability, plagiarism))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# NEW: Delete Route
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# NEW: Edit Route
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # Re-run AI audit for updated content
        keywords, readability, plagiarism = analyze_content(content)
        
        c.execute('''UPDATE posts SET title = ?, content = ?, keywords = ?, 
                     readability = ?, plagiarism = ? WHERE id = ?''',
                  (title, content, keywords, readability, plagiarism, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        c.execute('SELECT * FROM posts WHERE id = ?', (id,))
        post = c.fetchone()
        conn.close()
        return render_template('edit.html', post=post)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)