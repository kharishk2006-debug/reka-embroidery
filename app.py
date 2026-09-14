from flask import Flask, jsonify, request, send_from_directory, render_template_string
import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
import os

if os.environ.get("VERCEL"):
    DB = Path("/tmp/reviews.db")
else:
    DB = BASE / "reviews.db"
app = Flask(__name__, static_folder='assets', static_url_path='/assets')


def db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_conn() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            review TEXT NOT NULL,
            approved INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )''')
        conn.commit()


@app.route('/')
def home():
    return send_from_directory(BASE, 'index.html')


# Serve the root stylesheet too. The website links to /style.css, while
# Flask's static folder is configured for /assets.
@app.get('/style.css')
def root_stylesheet():
    return send_from_directory(BASE, 'style.css')


@app.get('/api/reviews')
def get_reviews():
    with db_conn() as conn:
        rows = conn.execute('''SELECT name, service, rating, review,
                                      strftime('%d %b %Y', created_at) AS date
                               FROM reviews
                               WHERE approved = 1
                               ORDER BY id DESC''').fetchall()
    return jsonify([dict(r) for r in rows])


@app.post('/api/reviews')
def add_review():
    data = request.get_json(silent=True) or request.form
    name = str(data.get('name', '')).strip()
    service = str(data.get('service', '')).strip()
    review = str(data.get('review', '')).strip()
    try:
        rating = int(data.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0

    if not name or not service or not review or rating not in range(1, 6):
        return jsonify({'message': 'Please complete all review fields and choose a rating.'}), 400
    if len(name) > 80 or len(service) > 100 or len(review) > 1000:
        return jsonify({'message': 'One of the fields is too long.'}), 400

    with db_conn() as conn:
        conn.execute('''INSERT INTO reviews(name, service, rating, review, approved, created_at)
                        VALUES (?, ?, ?, ?, 0, ?)''',
                     (name, service, rating, review, datetime.now().isoformat(timespec='seconds')))
        conn.commit()
    return jsonify({'message': 'Review submitted for approval.'}), 201


ADMIN_HTML = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>REKA Reviews Admin</title>
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;background:#fffaf9;color:#291c25;margin:0;padding:40px 20px}
.wrap{max-width:1000px;margin:auto}
h1{font-family:Georgia,serif;font-size:38px;margin:0 0 8px}
.meta{color:#766872;font-size:14px;margin:0 0 25px}
.toolbar{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:18px}
.count{font-size:13px;color:#766872}
.refresh{border:1px solid #ead9df;background:#fff;border-radius:20px;padding:9px 15px;cursor:pointer}
.card{background:#fff;border:1px solid #ead9df;border-radius:18px;padding:22px;margin:15px 0;box-shadow:0 8px 25px rgba(50,20,35,.05)}
.name{font-weight:700;font-size:17px}.service{color:#766872;font-size:13px}
.stars{margin-top:10px;letter-spacing:2px;color:#c88b2f}
.review{line-height:1.6;margin:12px 0;color:#40333b}
.status{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.08em;padding:5px 9px;border-radius:20px;background:#fff0f5;color:#b91f59}
.status.approved{background:#eef8f1;color:#287a45}
.date{font-size:11px;color:#988a92;margin-left:8px}
.actions{margin-top:16px;display:flex;gap:8px}
button.action{border:0;border-radius:20px;padding:10px 16px;cursor:pointer;font-weight:600}
.approve{background:#b91f59;color:white}.delete{background:#eee;color:#40333b}
.empty{padding:35px;text-align:center;border:1px dashed #ead9df;border-radius:18px;color:#766872;background:#fff}
.error{padding:20px;border:1px solid #efb6c8;border-radius:16px;background:#fff3f6;color:#a51645}
@media(max-width:600px){body{padding:25px 14px}h1{font-size:30px}.toolbar{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body>
<div class="wrap">
<h1>REKA — Review Approval</h1>
<p class="meta">Approve genuine customer reviews before they appear on the website.</p>
<div class="toolbar"><div class="count" id="count">Loading reviews…</div><button class="refresh" id="refresh">Refresh</button></div>
<div id="list"><div class="empty">Loading reviews…</div></div>
</div>
<script>
const list = document.getElementById('list');
const count = document.getElementById('count');
const refresh = document.getElementById('refresh');

function esc(value){
  return String(value ?? '').replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

function render(data){
  count.textContent = data.length + (data.length === 1 ? ' review' : ' reviews');
  if(!data.length){
    list.innerHTML = '<div class="empty">No reviews submitted yet.</div>';
    return;
  }
  list.innerHTML = data.map(function(x){
    const stars = '★'.repeat(Number(x.rating)) + '☆'.repeat(5-Number(x.rating));
    const status = Number(x.approved) === 1
      ? '<span class="status approved">APPROVED</span>'
      : '<span class="status">PENDING</span>';
    const approveButton = Number(x.approved) === 1
      ? ''
      : '<button class="action approve" data-id="'+x.id+'" data-action="approve">Approve</button>';
    return '<div class="card">'
      + '<div class="name">'+esc(x.name)+' <span class="service">— '+esc(x.service)+'</span></div>'
      + '<div class="stars">'+stars+'</div>'
      + '<div class="review">'+esc(x.review)+'</div>'
      + '<div>'+status+'<span class="date">'+esc(x.created_at)+'</span></div>'
      + '<div class="actions">'+approveButton+'<button class="action delete" data-id="'+x.id+'" data-action="delete">Delete</button></div>'
      + '</div>';
  }).join('');
}

async function load(){
  list.innerHTML = '<div class="empty">Loading reviews…</div>';
  try{
    const response = await fetch('/api/admin/reviews', {cache:'no-store'});
    if(!response.ok) throw new Error('Server returned '+response.status);
    const data = await response.json();
    render(Array.isArray(data) ? data : []);
  }catch(error){
    count.textContent = 'Unable to load reviews';
    list.innerHTML = '<div class="error"><strong>Could not load reviews.</strong><br>'+esc(error.message)+'<br><br>Make sure <b>python app.py</b> is still running, then refresh this page.</div>';
    console.error(error);
  }
}

async function act(id, action){
  try{
    const response = await fetch('/api/admin/reviews/'+encodeURIComponent(id), {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action:action})
    });
    if(!response.ok){
      const text = await response.text();
      throw new Error('Action failed ('+response.status+'): '+text);
    }
    await load();
  }catch(error){
    alert(error.message);
  }
}

list.addEventListener('click', function(event){
  const button = event.target.closest('button[data-id]');
  if(!button) return;
  act(button.dataset.id, button.dataset.action);
});
refresh.addEventListener('click', load);
load();
</script>
</body>
</html>'''


@app.get('/reka-control')
def admin():
    return render_template_string(ADMIN_HTML)


@app.get('/api/admin/reviews')
def admin_reviews():
    with db_conn() as conn:
        rows = conn.execute('SELECT id,name,service,rating,review,approved,created_at FROM reviews ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in rows])


@app.post('/api/admin/reviews/<int:review_id>')
def admin_action(review_id):
    action = (request.get_json(silent=True) or {}).get('action')
    with db_conn() as conn:
        if action == 'approve':
            conn.execute('UPDATE reviews SET approved=1 WHERE id=?', (review_id,))
        elif action == 'delete':
            conn.execute('DELETE FROM reviews WHERE id=?', (review_id,))
        else:
            return jsonify({'message': 'Invalid action'}), 400
        conn.commit()
    return jsonify({'ok': True})


init_db()

if __name__ == '__main__':
    app.run(debug=True)
