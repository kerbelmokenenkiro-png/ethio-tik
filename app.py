from flask import Flask, render_template_string, request, redirect, session, send_from_directory, jsonify
import sqlite3, hashlib, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
os.makedirs('uploads', exist_ok=True)

def init_db():
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT UNIQUE, 
        password TEXT, 
        bio TEXT, 
        profile_pic TEXT, 
        created_at TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY, 
        user_id INTEGER, 
        content TEXT, 
        image TEXT, 
        video TEXT, 
        timestamp TIMESTAMP, 
        likes INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY, 
        post_id INTEGER, 
        user_id INTEGER, 
        content TEXT, 
        timestamp TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        user_id INTEGER, 
        post_id INTEGER, 
        PRIMARY KEY (user_id, post_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER, 
        following_id INTEGER, 
        PRIMARY KEY (follower_id, following_id)
    )''')
    
    conn.commit()
    conn.close()
    migrate_db()

def migrate_db():
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE posts ADD COLUMN hashtags TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE posts ADD COLUMN is_premium_only INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE posts ADD COLUMN favorites INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE posts ADD COLUMN reposts INTEGER DEFAULT 0")
    except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER, 
        post_id INTEGER, 
        PRIMARY KEY (user_id, post_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reposts (
        user_id INTEGER, 
        post_id INTEGER, 
        PRIMARY KEY (user_id, post_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, 
        sender_id INTEGER, 
        receiver_id INTEGER, 
        content TEXT, 
        timestamp TIMESTAMP, 
        is_read INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY, 
        user_id INTEGER, 
        type TEXT, 
        from_user_id INTEGER, 
        post_id INTEGER, 
        is_read INTEGER DEFAULT 0, 
        timestamp TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY, 
        sender_id INTEGER, 
        receiver_id INTEGER, 
        amount INTEGER, 
        message TEXT, 
        timestamp TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("✅ ዳታቤዝ ተሻሽሏል!")

init_db()

@app.route('/')
def home():
    return render_template_string('''
    <style>body{font-family:Arial;text-align:center;padding:50px;background:linear-gradient(135deg,#078930,#FCDD09,#DA121A);color:#fff}.box{background:rgba(255,255,255,0.9);color:#000;padding:30px;border-radius:20px;max-width:400px;margin:auto}a{display:inline-block;margin:10px;padding:12px 25px;border-radius:30px;text-decoration:none;color:#fff;font-weight:bold}.g{background:#078930}.b{background:#1a73e8}.o{background:#f39c12}</style>
    <div class=box><h1>🎬 ቲክ ሶሻል</h1><p>የኢትዮጵያውያን ቪዲዮ መድረክ!</p><a href=/register class=g>📝 ይመዝገቡ</a><a href=/login class=b>🔑 ይግቡ</a><a href=/feed class=o>🎬 ቪዲዮዎች</a></div>
    ''')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        bio = request.form.get('bio','')
        try:
            conn = sqlite3.connect('social.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username,password,bio,created_at,coins) VALUES (?,?,?,?,?)", (username,password,bio,datetime.now(),100))
            conn.commit()
            conn.close()
            return "✅ ተመዝግበሃል! <a href='/login'>ይግቡ</a>"
        except:
            return "❌ ስም ተይዟል!"
    return '''
    <form method=post style=text-align:center;padding:40px;>
    <h2>📝 ይመዝገቡ</h2>
    <input name=username placeholder=ስም required><br><br>
    <input name=password type=password placeholder="የይለፍ ቃል" required><br><br>
    <textarea name=bio placeholder="ስለራስህ ትንሽ..."></textarea><br><br>
    <button type=submit>📝 ይመዝገቡ</button>
    </form>
    '''

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = sqlite3.connect('social.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect('/feed')
        return "❌ የተሳሳተ ስም ወይም የይለፍ ቃል"
    return '''
    <form method=post style=text-align:center;padding:40px;>
    <h2>🔑 ይግቡ</h2>
    <input name=username placeholder=ስም required><br><br>
    <input name=password type=password placeholder="የይለፍ ቃል" required><br><br>
    <button type=submit>🔑 ይግቡ</button>
    </form>
    '''

@app.route('/feed', methods=['GET','POST'])
def feed():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT is_premium FROM users WHERE id=?", (session['user_id'],))
    user_data = c.fetchone()
    is_premium = user_data[0] if user_data else 0
    conn.close()
    
    if request.method == 'POST':
        content = request.form.get('content','').strip()
        video = request.files.get('video')
        hashtags = request.form.get('hashtags','').strip()
        is_premium_only = 1 if request.form.get('is_premium_only') else 0
        vid_fn = None
        if video and video.filename:
            vid_fn = f"vid_{datetime.now().timestamp()}_{video.filename}"
            video.save(os.path.join('uploads', vid_fn))
        conn = sqlite3.connect('social.db')
        c = conn.cursor()
        c.execute("INSERT INTO posts (user_id,content,video,timestamp,hashtags,is_premium_only) VALUES (?,?,?,?,?,?)", 
                  (session['user_id'], content, vid_fn, datetime.now(), hashtags, is_premium_only))
        conn.commit()
        conn.close()
        return redirect('/feed')
    
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    
    if is_premium:
        c.execute('''SELECT posts.id, users.username, posts.content, posts.video, posts.timestamp, posts.likes, posts.favorites, posts.reposts, users.id, users.profile_pic, posts.hashtags, posts.is_premium_only, users.is_verified,
                     EXISTS(SELECT 1 FROM likes WHERE likes.post_id=posts.id AND likes.user_id=?) as liked,
                     EXISTS(SELECT 1 FROM favorites WHERE favorites.post_id=posts.id AND favorites.user_id=?) as favorited,
                     EXISTS(SELECT 1 FROM reposts WHERE reposts.post_id=posts.id AND reposts.user_id=?) as reposted
                     FROM posts JOIN users ON posts.user_id=users.id 
                     WHERE posts.video IS NOT NULL
                     ORDER BY posts.id DESC''', (session['user_id'], session['user_id'], session['user_id']))
    else:
        c.execute('''SELECT posts.id, users.username, posts.content, posts.video, posts.timestamp, posts.likes, posts.favorites, posts.reposts, users.id, users.profile_pic, posts.hashtags, posts.is_premium_only, users.is_verified,
                     EXISTS(SELECT 1 FROM likes WHERE likes.post_id=posts.id AND likes.user_id=?) as liked,
                     EXISTS(SELECT 1 FROM favorites WHERE favorites.post_id=posts.id AND favorites.user_id=?) as favorited,
                     EXISTS(SELECT 1 FROM reposts WHERE reposts.post_id=posts.id AND reposts.user_id=?) as reposted
                     FROM posts JOIN users ON posts.user_id=users.id 
                     WHERE posts.video IS NOT NULL AND posts.is_premium_only = 0
                     ORDER BY posts.id DESC''', (session['user_id'], session['user_id'], session['user_id']))
    posts = c.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>🎬 ቲክ ሶሻል</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #000; color: #fff; overflow: hidden; height: 100vh; touch-action: pan-y; }
            .video-container { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; scroll-behavior: smooth; -webkit-overflow-scrolling: touch; }
            .video-wrapper { height: 100vh; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; background: #000; touch-action: none; }
            .video-wrapper video { width: 100%; height: 100%; object-fit: cover; pointer-events: none; }
            .video-overlay { position: absolute; bottom: 0; left: 0; right: 0; padding: 80px 20px 30px; background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%); pointer-events: none; }
            .video-overlay .username { font-size: 17px; font-weight: 600; pointer-events: auto; text-decoration: none; color: #fff; display: inline-flex; align-items: center; gap: 6px; }
            .video-overlay .username:hover { text-decoration: underline; }
            .video-overlay .content { font-size: 15px; margin-top: 6px; pointer-events: auto; line-height: 1.4; max-width: 85%; }
            .video-overlay .hashtags { color: #4fc3f7; font-size: 14px; margin-top: 4px; pointer-events: auto; font-weight: 500; }
            .video-overlay .premium-badge { color: #ffd700; font-size: 11px; background: rgba(0,0,0,0.6); padding: 2px 10px; border-radius: 12px; display: inline-block; margin-top: 6px; border: 1px solid rgba(255,215,0,0.3); }
            .video-overlay .verified-badge { color: #4fc3f7; font-size: 16px; }
            .video-actions { position: absolute; right: 16px; bottom: 120px; display: flex; flex-direction: column; gap: 18px; align-items: center; pointer-events: auto; z-index: 10; }
            .video-actions a { color: #fff; text-decoration: none; font-size: 26px; display: flex; flex-direction: column; align-items: center; gap: 2px; transition: all 0.15s ease; cursor: pointer; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
            .video-actions a:hover { transform: scale(1.1); }
            .video-actions a:active { transform: scale(0.9); }
            .video-actions .count { font-size: 12px; font-weight: 600; letter-spacing: 0.3px; }
            .like-btn.liked { color: #ff2d55; }
            .like-btn.liked .count { color: #ff2d55; }
            .favorite-btn.favorited { color: #ffd700; }
            .favorite-btn.favorited .count { color: #ffd700; }
            .video-actions .profile-icon { width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #e74c3c, #f39c12); display: flex; align-items: center; justify-content: center; font-size: 20px; border: 2.5px solid #fff; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.6); transition: transform 0.2s; touch-action: manipulation; }
            .video-actions .profile-icon:hover { transform: scale(1.05); }
            .video-actions .profile-icon img { width: 100%; height: 100%; object-fit: cover; }
            .upload-btn { position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #fff, #f0f0f0); color: #000; padding: 12px 28px; border-radius: 30px; text-decoration: none; font-weight: 700; font-size: 14px; z-index: 20; box-shadow: 0 4px 20px rgba(0,0,0,0.6); pointer-events: auto; letter-spacing: 0.5px; transition: all 0.2s; touch-action: manipulation; }
            .upload-btn:hover { background: #fff; transform: translateX(-50%) scale(1.03); }
            .upload-btn:active { transform: translateX(-50%) scale(0.95); }
            .no-videos { color: #666; text-align: center; padding: 100px 20px; font-size: 18px; }
            .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); display: flex; justify-content: space-around; padding: 8px 0 14px; border-top: 0.5px solid rgba(255,255,255,0.06); max-width: 600px; margin: auto; z-index: 30; pointer-events: auto; }
            .bottom-nav a { color: #888; text-decoration: none; font-size: 22px; display: flex; flex-direction: column; align-items: center; gap: 1px; transition: color 0.2s; padding: 4px 12px; border-radius: 8px; touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
            .bottom-nav a.active { color: #fff; }
            .bottom-nav a:hover { color: #fff; }
            .bottom-nav .label { font-size: 10px; font-weight: 500; letter-spacing: 0.3px; }
            .top-bar { position: fixed; top: 0; left: 0; right: 0; padding: 12px 20px; background: rgba(0,0,0,0.5); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); display: flex; justify-content: space-between; align-items: center; z-index: 20; max-width: 600px; margin: auto; pointer-events: auto; }
            .top-bar .logo { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: -0.5px; background: linear-gradient(135deg, #ff2d55, #ff6b35); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .top-bar a { color: #fff; text-decoration: none; font-size: 20px; transition: opacity 0.2s; padding: 4px; touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
            .top-bar a:hover { opacity: 0.7; }
            .top-bar .icons { display: flex; gap: 12px; align-items: center; }
            .search-bar { display: flex; gap: 6px; align-items: center; }
            .search-bar input { background: rgba(255,255,255,0.08); border: none; border-radius: 20px; padding: 6px 14px; color: #fff; font-size: 13px; width: 110px; outline: none; transition: all 0.3s; }
            .search-bar input:focus { background: rgba(255,255,255,0.15); width: 150px; }
            .search-bar input::placeholder { color: rgba(255,255,255,0.4); }
            .search-bar button { background: #ff2d55; border: none; border-radius: 50%; color: #fff; padding: 6px 8px; cursor: pointer; font-size: 14px; transition: all 0.2s; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; touch-action: manipulation; }
            .search-bar button:hover { background: #ff1744; transform: scale(1.05); }
            .ad-banner { background: linear-gradient(135deg, #ff2d55, #ff6b35); padding: 10px 16px; text-align: center; font-size: 13px; font-weight: 600; cursor: pointer; letter-spacing: 0.3px; position: fixed; top: 56px; left: 0; right: 0; max-width: 600px; margin: auto; z-index: 15; }
            .ad-banner a { color: #fff; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; }
            .like-burst { position: absolute; color: #ff2d55; font-size: 40px; font-weight: 700; pointer-events: none; animation: floatUp 0.8s ease-out forwards; z-index: 50; }
            @keyframes floatUp { 0% { opacity: 1; transform: translateY(0) scale(0.5); } 100% { opacity: 0; transform: translateY(-80px) scale(1.2); } }
        </style>
    </head>
    <body>
        <div class="top-bar">
            <span class="logo">🎬 ቲክ ሶሻል</span>
            <div class="search-bar">
                <form method="get" action="/feed" style="display:flex;gap:6px;align-items:center;">
                    <input type="text" name="tag" placeholder="#ሃሽታግ">
                    <button type="submit">🔍</button>
                </form>
            </div>
            <div class="icons">
                <a href="/chat">💬</a>
                <a href="/premium">👑</a>
                <a href="/logout">🚪</a>
            </div>
        </div>
        <div class="ad-banner">
            <a href="/premium">📢 ፕሪሚየም ይሁኑ! ማስታወቂያዎችን ያስወግዱ እና ልዩ ባህሪያት ያግኙ! 👑</a>
        </div>
        <div class="video-container" id="videoContainer">
    '''
    
    if posts:
        for p in posts:
            pid, un, cont, vid, ts, likes, favs, reposts, uid, ppic, hashtags, is_premium_only, is_verified, liked, favorited, reposted = p
            ts_str = ts[:16] if ts else 'አሁን'
            profile_img_html = f'<img src="/uploads/{ppic}">' if ppic else '👤'
            
            premium_badge = '<span class="premium-badge">👑 ፕሪሚየም</span>' if is_premium_only else ''
            verified_badge = '<span class="verified-badge">✅</span>' if is_verified else ''
            
            hashtag_html = ''
            if hashtags:
                hashtag_html = f'<div class="hashtags">#️⃣ {hashtags}</div>'
            
            html += f'''
            <div class="video-wrapper" data-post="{pid}">
                <video loop muted playsinline>
                    <source src="/uploads/{vid}">
                </video>
                <div class="video-overlay">
                    <a href="/profile/{uid}" class="username">@{un} {verified_badge}</a>
                    <div class="content">{cont}</div>
                    {hashtag_html}
                    {premium_badge}
                </div>
                <div class="video-actions">
                    <a href="/profile/{uid}"><div class="profile-icon">{profile_img_html}</div></a>
                    <a href="#" onclick="event.preventDefault(); toggleLike({pid});" class="like-btn {'liked' if liked else ''}" ontouchstart="event.preventDefault(); toggleLike({pid});">
                        <span id="like-icon-{pid}">{'❤️' if liked else '🤍'}</span>
                        <span class="count" id="like-count-{pid}">{likes}</span>
                    </a>
                    <a href="/comment/{pid}">💬<span class="count">0</span></a>
                    <a href="#" onclick="event.preventDefault(); toggleFavorite({pid});" class="favorite-btn {'favorited' if favorited else ''}" ontouchstart="event.preventDefault(); toggleFavorite({pid});">
                        <span id="fav-icon-{pid}">{'⭐' if favorited else '☆'}</span>
                        <span class="count" id="fav-count-{pid}">{favs}</span>
                    </a>
                    <a href="#" onclick="event.preventDefault(); toggleRepost({pid});" ontouchstart="event.preventDefault(); toggleRepost({pid});">
                        <span id="repost-icon-{pid}">{'🔄' if reposted else '🔁'}</span>
                        <span class="count" id="repost-count-{pid}">{reposts}</span>
                    </a>
                    <a href="#" onclick="event.preventDefault(); sharePost({pid}, '{un}');" ontouchstart="event.preventDefault(); sharePost({pid}, '{un}');">📤<span class="count">ሼር</span></a>
                    <a href="#" onclick="event.preventDefault(); copyLink({pid});" ontouchstart="event.preventDefault(); copyLink({pid});">🔗<span class="count">ሊንክ</span></a>
                    <a href="/donate/{uid}">🎁<span class="count">ልገሳ</span></a>
                    {'<a href="/delete/'+str(pid)+'">🗑️<span class="count">ሰርዝ</span></a>' if uid == session['user_id'] else ''}
                </div>
            </div>
            '''
    else:
        html += '<div class="no-videos">🎬 ምንም ቪዲዮ የለም!<br>የመጀመሪያውን ቪዲዮ ስቀል!</div>'
    
    html += '''
        </div>
        <a href="/upload" class="upload-btn">📤 ቪዲዮ ስቀል</a>
        <div class="bottom-nav">
            <a href="/feed" class="active">🏠<span class="label">መነሻ</span></a>
            <a href="/search">🔍<span class="label">ፈልግ</span></a>
            <a href="/chat">💬<span class="label">ውይይት</span></a>
            <a href="/premium">👑<span class="label">ፕሪሚየም</span></a>
            <a href="/profile/''' + str(session['user_id']) + '''">👤<span class="label">ፕሮፋይል</span></a>
        </div>
        <script>
            // ቪዲዮ አጫዋች
            var videos = document.querySelectorAll('.video-wrapper video');
            var observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.muted = false;
                        entry.target.play();
                    } else {
                        entry.target.muted = true;
                        entry.target.pause();
                    }
                });
            }, { threshold: 0.5 });
            videos.forEach(function(video) { observer.observe(video); });
            
            // ላይክ
            function toggleLike(postId) {
                fetch('/like_ajax/' + postId).then(function(r) { return r.json(); }).then(function(data) {
                    var icon = document.getElementById('like-icon-' + postId);
                    var count = document.getElementById('like-count-' + postId);
                    icon.textContent = data.liked ? '❤️' : '🤍';
                    count.textContent = data.likes;
                    icon.parentElement.classList.toggle('liked', data.liked);
                    
                    if (data.liked) {
                        var wrapper = document.querySelector('[data-post="' + postId + '"]');
                        var burst = document.createElement('div');
                        burst.className = 'like-burst';
                        burst.textContent = '❤️';
                        burst.style.left = (window.innerWidth - 80) + 'px';
                        burst.style.bottom = '220px';
                        wrapper.appendChild(burst);
                        setTimeout(function() { burst.remove(); }, 800);
                    }
                });
            }
            
            // ፌቨራይት
            function toggleFavorite(postId) {
                fetch('/favorite_ajax/' + postId).then(function(r) { return r.json(); }).then(function(data) {
                    document.getElementById('fav-icon-' + postId).textContent = data.favorited ? '⭐' : '☆';
                    document.getElementById('fav-count-' + postId).textContent = data.favorites;
                });
            }
            
            // ሪፖስት
            function toggleRepost(postId) {
                fetch('/repost_ajax/' + postId).then(function(r) { return r.json(); }).then(function(data) {
                    document.getElementById('repost-icon-' + postId).textContent = data.reposted ? '🔄' : '🔁';
                    document.getElementById('repost-count-' + postId).textContent = data.reposts;
                });
            }
            
            // ሼር
            function sharePost(postId, username) {
                var url = window.location.origin + '/feed?post=' + postId;
                if (navigator.share) {
                    navigator.share({ title: username, text: '🎬 ቲክ ሶሻል ቪዲዮ!', url: url });
                } else {
                    navigator.clipboard.writeText(url);
                    alert('✅ ሊንክ ተቀድቷል!');
                }
            }
            
            // ሊንክ ቅዳ
            function copyLink(postId) {
                var url = window.location.origin + '/feed?post=' + postId;
                navigator.clipboard.writeText(url);
                alert('✅ ሊንክ ተቀድቷል: ' + url);
            }
        </script>
    </body>
    </html>
    '''
    return html

# ============ የቀሩት ተግባራት ============

@app.route('/premium')
def premium():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT username, is_premium, is_verified, coins FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>👑 ፕሪሚየም</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,Arial,sans-serif;background:#000;color:#fff}}.container{{max-width:600px;margin:auto;background:#0a0a0a;min-height:100vh}}.top-bar{{padding:16px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #222}}.top-bar a{{color:#fff;text-decoration:none;font-size:24px}}.top-bar .title{{font-size:18px;font-weight:bold}}.card{{background:#1a1a1a;margin:16px;padding:20px;border-radius:16px;text-align:center}}.card .price{{font-size:32px;font-weight:bold;color:#ffd700}}.card .desc{{color:#888;margin:10px 0}}.btn{{background:#ffd700;color:#000;border:none;padding:12px 30px;border-radius:25px;font-size:16px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block}}.btn:hover{{background:#f0c000}}.btn-blue{{background:#1a73e8;color:#fff}}.btn-blue:hover{{background:#1557b0}}.features{{text-align:left;padding:0 20px;list-style:none}}.features li{{padding:8px 0;border-bottom:1px solid #1a1a1a}}.features li:before{{content:"✅ ";color:#ffd700}}.bottom-nav{{position:fixed;bottom:0;left:0;right:0;background:#0a0a0a;display:flex;justify-content:space-around;padding:10px 0;border-top:1px solid #222;max-width:600px;margin:auto}}.bottom-nav a{{color:#888;text-decoration:none;font-size:22px;display:flex;flex-direction:column;align-items:center;gap:2px}}.bottom-nav a.active{{color:#1a73e8}}.bottom-nav .label{{font-size:10px}}
    </style>
    </head>
    <body>
        <div class=container>
            <div class=top-bar><a href=/feed>‹</a><span class=title>👑 ፕሪሚየም</span><span></span></div>
            <div class=card><div class=price>👑 {user[0]}</div>
            <div class=desc>{"✅ ፕሪሚየም አባል" if user[1] else "❌ መደበኛ ተጠቃሚ"}</div>
            <div class=desc>{"✅ የተረጋገጠ" if user[2] else "❌ ያልተረጋገጠ"}</div>
            <div class=desc>🪙 {user[3]} ሳንቲም</div>
            </div>
            <div class=card><div class=price>👑 ፕሪሚየም ይሁኑ</div>
            <div class=desc>በወር 50 ብር ብቻ!</div>
            <ul class=features>
                <li>ማስታወቂያ የለም</li>
                <li>ፕሪሚየም ቪዲዮዎችን ማየት</li>
                <li>የተረጋገጠ ምልክት ✅</li>
                <li>ልዩ ስቲከሮች</li>
                <li>ቅድሚያ ድጋፍ</li>
            </ul>
            <br>
            <a href="/upgrade_premium" class="btn">👑 አሁን ይመዝገቡ</a>
            </div>
            <div class=card><div class=price>🪙 ሳንቲም</div>
            <div class=desc>ለሌሎች ልገሳ ለመስጠት ሳንቲም ያግኙ!</div>
            <br>
            <a href="/buy_coins" class="btn btn-blue">🪙 ሳንቲም ግዙ</a>
            </div>
        </div>
        <div class=bottom-nav>
            <a href=/feed>🏠<span class=label>መነሻ</span></a>
            <a href=/search>🔍<span class=label>ፈልግ</span></a>
            <a href=/chat>💬<span class=label>ውይይት</span></a>
            <a href=/premium class=active>👑<span class=label>ፕሪሚየም</span></a>
            <a href=/profile/{session['user_id']}>👤<span class=label>ፕሮፋይል</span></a>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/upgrade_premium')
def upgrade_premium():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1, is_verified=1, coins=coins+500 WHERE id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    return redirect('/premium')

@app.route('/buy_coins', methods=['GET', 'POST'])
def buy_coins():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        amount = int(request.form.get('amount', 100))
        conn = sqlite3.connect('social.db')
        c = conn.cursor()
        c.execute("UPDATE users SET coins=coins+? WHERE id=?", (amount, session['user_id']))
        conn.commit()
        conn.close()
        return redirect('/premium')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🪙 ሳንቲም ግዙ</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}}.container{{background:#1a1a1a;padding:40px;border-radius:20px;max-width:400px;width:100%;text-align:center}}button{{background:#ffd700;color:#000;border:none;padding:12px 30px;border-radius:25px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;margin:10px 0}}button:hover{{background:#f0c000}}select{{width:100%;padding:12px;border-radius:12px;border:1px solid #333;background:#222;color:#fff;font-size:16px;margin:10px 0}}a{{color:#1a73e8;text-decoration:none}}
    </style>
    </head>
    <body>
        <div class=container><h2>🪙 ሳንቲም ግዙ</h2>
        <form method=post>
        <select name=amount>
            <option value=100>100 ሳንቲም - 10 ብር</option>
            <option value=500>500 ሳንቲም - 40 ብር</option>
            <option value=1000>1000 ሳንቲም - 70 ብር</option>
            <option value=5000>5000 ሳንቲም - 300 ብር</option>
        </select>
        <button type=submit>🪙 ግዙ</button>
        </form><br><a href=/premium>⬅️ ወደ ፕሪሚየም</a></div>
    </body>
    </html>
    '''
    return html

@app.route('/donate/<int:user_id>', methods=['GET', 'POST'])
def donate(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    if user_id == session['user_id']:
        return redirect('/feed')
    
    if request.method == 'POST':
        amount = int(request.form.get('amount', 10))
        message = request.form.get('message', '').strip()
        conn = sqlite3.connect('social.db')
        c = conn.cursor()
        c.execute("SELECT coins FROM users WHERE id=?", (session['user_id'],))
        sender_coins = c.fetchone()[0]
        if sender_coins < amount:
            conn.close()
            return "❌ በቂ ሳንቲም የለህም!"
        c.execute("UPDATE users SET coins=coins-? WHERE id=?", (amount, session['user_id']))
        c.execute("UPDATE users SET coins=coins+? WHERE id=?", (amount, user_id))
        c.execute("INSERT INTO donations (sender_id, receiver_id, amount, message, timestamp) VALUES (?,?,?,?,?)",
                  (session['user_id'], user_id, amount, message, datetime.now()))
        c.execute("INSERT INTO notifications (user_id, type, from_user_id, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, 'donation', session['user_id'], datetime.now()))
        conn.commit()
        conn.close()
        return redirect('/profile/' + str(user_id))
    
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT username, coins FROM users WHERE id=?", (user_id,))
    receiver = c.fetchone()
    c.execute("SELECT coins FROM users WHERE id=?", (session['user_id'],))
    sender_coins = c.fetchone()[0]
    conn.close()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🎁 ልገሳ</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}}.container{{background:#1a1a1a;padding:40px;border-radius:20px;max-width:400px;width:100%;text-align:center}}input,textarea{{width:100%;padding:12px;border-radius:12px;border:1px solid #333;background:#222;color:#fff;margin:10px 0}}button{{background:#ffd700;color:#000;border:none;padding:12px 30px;border-radius:25px;font-size:16px;font-weight:bold;cursor:pointer;width:100%}}button:hover{{background:#f0c000}}a{{color:#1a73e8;text-decoration:none}}
    </style>
    </head>
    <body>
        <div class=container><h2>🎁 ለ {receiver[0]} ልገሳ</h2>
        <p>🪙 ሳንቲምህ: {sender_coins}</p>
        <form method=post>
        <input type=number name=amount placeholder="ሳንቲም ብዛት" min=1 max={sender_coins} required>
        <textarea name=message placeholder="መልዕክት..."></textarea>
        <button type=submit>🎁 ለግስ</button>
        </form><br><a href=/feed>⬅️ ወደ ቪዲዮዎች</a></div>
    </body>
    </html>
    '''
    return html

@app.route('/like_ajax/<int:post_id>')
def like_ajax(post_id):
    if 'user_id' not in session:
        return {'liked': False, 'likes': 0}
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
    existing = c.fetchone()
    if existing:
        c.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
        c.execute("UPDATE posts SET likes = likes - 1 WHERE id=?", (post_id,))
        liked = False
    else:
        c.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (session['user_id'], post_id))
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
        liked = True
    c.execute("SELECT likes FROM posts WHERE id=?", (post_id,))
    likes = c.fetchone()[0]
    conn.commit()
    conn.close()
    return {'liked': liked, 'likes': likes}

@app.route('/favorite_ajax/<int:post_id>')
def favorite_ajax(post_id):
    if 'user_id' not in session:
        return {'favorited': False, 'favorites': 0}
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT * FROM favorites WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
    existing = c.fetchone()
    if existing:
        c.execute("DELETE FROM favorites WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
        c.execute("UPDATE posts SET favorites = favorites - 1 WHERE id=?", (post_id,))
        favorited = False
    else:
        c.execute("INSERT INTO favorites (user_id, post_id) VALUES (?, ?)", (session['user_id'], post_id))
        c.execute("UPDATE posts SET favorites = favorites + 1 WHERE id=?", (post_id,))
        favorited = True
    c.execute("SELECT favorites FROM posts WHERE id=?", (post_id,))
    favorites = c.fetchone()[0]
    conn.commit()
    conn.close()
    return {'favorited': favorited, 'favorites': favorites}

@app.route('/repost_ajax/<int:post_id>')
def repost_ajax(post_id):
    if 'user_id' not in session:
        return {'reposted': False, 'reposts': 0}
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reposts WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
    existing = c.fetchone()
    if existing:
        c.execute("DELETE FROM reposts WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
        c.execute("UPDATE posts SET reposts = reposts - 1 WHERE id=?", (post_id,))
        reposted = False
    else:
        c.execute("INSERT INTO reposts (user_id, post_id) VALUES (?, ?)", (session['user_id'], post_id))
        c.execute("UPDATE posts SET reposts = reposts + 1 WHERE id=?", (post_id,))
        reposted = True
    c.execute("SELECT reposts FROM posts WHERE id=?", (post_id,))
    reposts = c.fetchone()[0]
    conn.commit()
    conn.close()
    return {'reposted': reposted, 'reposts': reposts}

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT user_id, video FROM posts WHERE id=?", (post_id,))
    post = c.fetchone()
    if post and post[0] == session['user_id']:
        if post[1] and os.path.exists(os.path.join('uploads', post[1])):
            os.remove(os.path.join('uploads', post[1]))
        c.execute("DELETE FROM posts WHERE id=?", (post_id,))
        c.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id=?", (post_id,))
        c.execute("DELETE FROM favorites WHERE post_id=?", (post_id,))
        c.execute("DELETE FROM reposts WHERE post_id=?", (post_id,))
        conn.commit()
    conn.close()
    return redirect('/feed')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        video = request.files.get('video')
        hashtags = request.form.get('hashtags', '').strip()
        is_premium_only = 1 if request.form.get('is_premium_only') else 0
        if video and video.filename:
            vid_fn = f"vid_{datetime.now().timestamp()}_{video.filename}"
            video.save(os.path.join('uploads', vid_fn))
            conn = sqlite3.connect('social.db')
            c = conn.cursor()
            c.execute("INSERT INTO posts (user_id, content, video, timestamp, hashtags, is_premium_only) VALUES (?, ?, ?, ?, ?, ?)",
                      (session['user_id'], content, vid_fn, datetime.now(), hashtags, is_premium_only))
            conn.commit()
            conn.close()
            return redirect('/feed')
        return "❌ እባክህ ቪዲዮ ምረጥ!"
    return '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>📤 ቪዲዮ ስቀል</title>
    <style>body{font-family:Arial;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px}.upload-container{background:#1a1a1a;padding:40px;border-radius:20px;max-width:500px;width:100%;text-align:center}h2{margin-bottom:20px}input[type=file]{background:#333;color:#fff;padding:20px;border-radius:12px;width:100%;margin:10px 0;border:2px dashed #555;cursor:pointer}textarea{width:100%;padding:12px;border-radius:12px;border:none;background:#222;color:#fff;margin:10px 0;min-height:80px}button{background:#1a73e8;color:#fff;border:none;padding:14px 40px;border-radius:30px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;margin-top:10px}button:hover{background:#1557b0}a{color:#1a73e8;text-decoration:none}
    .checkbox{display:flex;align-items:center;gap:10px;margin:10px 0;color:#fff}
    </style>
    </head>
    <body>
        <div class=upload-container><h2>📤 ቪዲዮ ስቀል</h2>
        <form method=post enctype=multipart/form-data>
        <input type=file name=video accept="video/*" required>
        <textarea name=content placeholder="ስለ ቪዲዮው ትንሽ ጻፍ..."></textarea>
        <input type=text name=hashtags placeholder="#ሃሽታግ (ለምሳሌ #ኢትዮጵያ #ቲክቶክ)" style="width:100%;padding:10px;border-radius:8px;border:none;background:#222;color:#fff;margin:10px 0;">
        <div class=checkbox><input type=checkbox name=is_premium_only id=premium><label for=premium>👑 ፕሪሚየም ተጠቃሚዎች ብቻ</label></div>
        <button type=submit>📤 ለጥፍ</button>
        </form><br><a href=/feed>⬅️ ወደ ቪዲዮዎች</a></div>
    </body>
    </html>
    '''

@app.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT id, username, bio, profile_pic, created_at, is_premium, is_verified, coins FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return "❌ ተጠቃሚ አልተገኘም"
    c.execute("SELECT COUNT(*) FROM posts WHERE user_id=? AND video IS NOT NULL", (user_id,))
    post_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", (user_id,))
    follower_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM follows WHERE follower_id=?", (user_id,))
    following_count = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(likes), 0) FROM posts WHERE user_id=?", (user_id,))
    total_likes = c.fetchone()[0]
    c.execute("SELECT * FROM follows WHERE follower_id=? AND following_id=?", (session['user_id'], user_id))
    is_following = c.fetchone() is not None
    c.execute("SELECT id, content, video, timestamp, likes FROM posts WHERE user_id=? AND video IS NOT NULL ORDER BY id DESC", (user_id,))
    user_posts = c.fetchall()
    conn.close()
    
    profile_img_html = f'<img src="/uploads/{user[3]}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">' if user[3] else '👤'
    premium_badge = '👑' if user[5] else ''
    verified_badge = '✅' if user[6] else ''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>👤 {user[1]}</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,Arial,sans-serif;background:#000;color:#fff}}.profile-container{{max-width:600px;margin:auto;background:#0a0a0a;min-height:100vh}}.top-bar{{padding:16px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #222}}.top-bar a{{color:#fff;text-decoration:none;font-size:24px}}.top-bar .username{{font-size:18px;font-weight:bold}}.profile-header{{padding:20px;display:flex;align-items:center;gap:20px}}.profile-img{{width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#e74c3c,#f39c12);display:flex;align-items:center;justify-content:center;font-size:40px;flex-shrink:0;overflow:hidden}}.profile-info{{flex:1}}.profile-info .name{{font-size:20px;font-weight:bold}}.profile-info .bio{{color:#888;font-size:14px;margin-top:4px}}.profile-info .badges{{font-size:16px;margin-top:4px}}.stats{{display:flex;justify-content:space-around;padding:16px 20px;border-top:1px solid #222;border-bottom:1px solid #222}}.stat{{text-align:center}}.stat-number{{font-size:20px;font-weight:bold}}.stat-label{{color:#888;font-size:13px}}.posts-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;padding:2px}}.post-item{{aspect-ratio:1;background:#1a1a1a;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}}.post-item video{{width:100%;height:100%;object-fit:cover}}.post-item .post-overlay{{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,0.7));padding:10px;display:flex;justify-content:space-around;color:#fff;font-size:12px}}.no-posts{{grid-column:1/-1;text-align:center;color:#666;padding:60px 0;font-size:16px}}.bottom-nav{{position:fixed;bottom:0;left:0;right:0;background:#0a0a0a;display:flex;justify-content:space-around;padding:10px 0;border-top:1px solid #222;max-width:600px;margin:auto}}.bottom-nav a{{color:#888;text-decoration:none;font-size:22px;transition:0.3s}}.bottom-nav a.active{{color:#1a73e8}}.follow-btn{{background:#1a73e8;color:#fff;border:none;padding:8px 30px;border-radius:20px;font-size:14px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin-top:8px}}.follow-btn.unfollow{{background:#333}}.upload-pic-btn{{background:transparent;border:1px solid #333;color:#fff;padding:4px 12px;border-radius:12px;font-size:11px;cursor:pointer;text-decoration:none;display:inline-block;margin-top:4px}}.upload-pic-btn:hover{{background:#222}}.donate-btn{{background:#ffd700;color:#000;padding:4px 12px;border-radius:12px;font-size:11px;cursor:pointer;text-decoration:none;display:inline-block;margin-top:4px}}
    </style>
    </head>
    <body>
        <div class=profile-container>
            <div class=top-bar><a href=/feed>‹</a><span class=username>{user[1]} {premium_badge} {verified_badge}</span><a href=/logout>⋯</a></div>
            <div class=profile-header><div class=profile-img>{profile_img_html}</div>
                <div class=profile-info><div class=name>{user[1]} {premium_badge}</div>
                <div class=bio>{user[2] or 'ስለራሱ አልተናገረም'}</div>
                <div class=badges>🪙 {user[7]} ሳንቲም</div>
                <a href=/follow/{user[0]} class="follow-btn {'unfollow' if is_following else ''}">{'ይከተሉ' if not is_following else 'አይከተሉም'}</a><br>
                <a href=/upload_profile_pic class=upload-pic-btn>📸 ፎቶ ለጥፍ</a>
                <a href=/donate/{user[0]} class=donate-btn>🎁 ልገሳ</a></div>
            </div>
            <div class=stats>
                <div class=stat><div class=stat-number>{post_count}</div><div class=stat-label>ልጥፎች</div></div>
                <div class=stat><div class=stat-number>{follower_count}</div><div class=stat-label>ተከታዮች</div></div>
                <div class=stat><div class=stat-number>{following_count}</div><div class=stat-label>የሚከተላቸው</div></div>
                <div class=stat><div class=stat-number>{total_likes}</div><div class=stat-label>ላይክ</div></div>
            </div>
            <div class=posts-grid>
    '''
    if user_posts:
        for p in user_posts[:9]:
            pid, cont, vid, ts, likes = p
            html += f'<div class=post-item><video controls><source src=/uploads/{vid}></video><div class=post-overlay><span>❤️ {likes}</span></div></div>'
    else:
        html += '<div class=no-posts>😅 ምንም ቪዲዮ የለም</div>'
    html += f'''
            </div>
        </div>
        <div class=bottom-nav>
            <a href=/feed>🏠</a>
            <a href=/search>🔍</a>
            <a href=/chat>💬</a>
            <a href=/premium>👑</a>
            <a href=/profile/{session['user_id']} class=active>👤</a>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/upload_profile_pic', methods=['GET', 'POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        if 'profile_pic' not in request.files:
            return redirect('/profile/' + str(session['user_id']))
        file = request.files['profile_pic']
        if file and file.filename:
            filename = f"profile_{session['user_id']}_{datetime.now().timestamp()}_{file.filename}"
            file.save(os.path.join('uploads', filename))
            conn = sqlite3.connect('social.db')
            c = conn.cursor()
            c.execute("UPDATE users SET profile_pic=? WHERE id=?", (filename, session['user_id']))
            conn.commit()
            conn.close()
            return redirect('/profile/' + str(session['user_id']))
    return '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>📸 ፕሮፋይል ፎቶ</title>
    <style>body{font-family:Arial;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px}.upload-container{background:#1a1a1a;padding:40px;border-radius:20px;max-width:400px;width:100%;text-align:center}input[type=file]{background:#333;color:#fff;padding:20px;border-radius:12px;width:100%;margin:10px 0;border:2px dashed #555;cursor:pointer}button{background:#1a73e8;color:#fff;border:none;padding:14px 40px;border-radius:30px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;margin-top:10px}button:hover{background:#1557b0}a{color:#1a73e8;text-decoration:none}</style>
    </head>
    <body>
        <div class=upload-container><h2>📸 ፕሮፋይል ፎቶ ለጥፍ</h2>
        <form method=post enctype=multipart/form-data>
        <input type=file name=profile_pic accept="image/*" required>
        <button type=submit>📸 ለጥፍ</button>
        </form><br><a href=/profile/''' + str(session['user_id']) + '''>⬅️ ወደ ፕሮፋይል</a></div>
    </body>
    </html>
    '''

@app.route('/like/<int:post_id>')
def like_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
    existing = c.fetchone()
    if existing:
        c.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (session['user_id'], post_id))
        c.execute("UPDATE posts SET likes = likes - 1 WHERE id=?", (post_id,))
    else:
        c.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (session['user_id'], post_id))
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or '/feed')

@app.route('/comment/<int:post_id>', methods=['GET','POST'])
def comment(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        content = request.form.get('content','').strip()
        if content:
            conn = sqlite3.connect('social.db')
            c = conn.cursor()
            c.execute("INSERT INTO comments (post_id,user_id,content,timestamp) VALUES (?,?,?,?)", (post_id, session['user_id'], content, datetime.now()))
            c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
            post_owner = c.fetchone()
            if post_owner and post_owner[0] != session['user_id']:
                c.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                          (post_owner[0], 'comment', session['user_id'], post_id, datetime.now()))
            conn.commit()
            conn.close()
        return redirect('/feed')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT users.username, comments.content, comments.timestamp FROM comments JOIN users ON comments.user_id=users.id WHERE comments.post_id=? ORDER BY comments.id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    html = '<style>body{font-family:Arial;padding:20px;max-width:600px;margin:auto;background:#0a0a0a;color:#fff}.comment{background:#1a1a1a;padding:10px;border-radius:8px;margin-bottom:10px}.comment-user{font-weight:bold;color:#1a73e8}textarea{width:100%;padding:10px;border-radius:8px;border:1px solid #333;background:#222;color:#fff}button{background:#1a73e8;color:#fff;border:none;padding:10px 20px;border-radius:25px;cursor:pointer}a{color:#1a73e8}</style><h2>💬 አስተያየቶች</h2>'
    if comments:
        for un, cont, ts in comments:
            html += f'<div class=comment><span class=comment-user>{un}</span>: {cont}</div>'
    else:
        html += '<p style=color:#666>😅 ምንም አስተያየት የለም!</p>'
    html += '<form method=post><textarea name=content placeholder="አስተያየትህን ጻፍ..."></textarea><br><button type=submit>💬 ለጥፍ</button></form><a href=/feed>⬅️ ወደ ቪዲዮዎች</a>'
    return html

@app.route('/follow/<int:user_id>')
def follow(user_id):
    if 'user_id' not in session or user_id == session['user_id']:
        return redirect('/feed')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT * FROM follows WHERE follower_id=? AND following_id=?", (session['user_id'], user_id))
    existing = c.fetchone()
    if existing:
        c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (session['user_id'], user_id))
    else:
        c.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (session['user_id'], user_id))
        c.execute("INSERT INTO notifications (user_id, type, from_user_id, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, 'follow', session['user_id'], datetime.now()))
    conn.commit()
    conn.close()
    return redirect(request.referrer or '/feed')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute("SELECT id, username, profile_pic FROM users WHERE id != ?", (session['user_id'],))
    users = c.fetchall()
    c.execute("SELECT sender_id, COUNT(*) FROM messages WHERE receiver_id=? AND is_read=0 GROUP BY sender_id", (session['user_id'],))
    unread = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    html = '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>💬 ውይይት</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,Arial,sans-serif;background:#000;color:#fff}.chat-container{max-width:600px;margin:auto;background:#0a0a0a;min-height:100vh}.top-bar{padding:16px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #222}.top-bar a{color:#fff;text-decoration:none;font-size:24px}.top-bar .title{font-size:18px;font-weight:bold}.user-item{display:flex;align-items:center;padding:16px 20px;border-bottom:1px solid #1a1a1a;text-decoration:none;color:#fff;gap:12px}.user-item:hover{background:#1a1a1a}.user-img{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#e74c3c,#f39c12);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;overflow:hidden}.user-img img{width:100%;height:100%;object-fit:cover}.user-info{flex:1}.user-info .name{font-weight:bold}.user-info .status{color:#888;font-size:13px}.unread-badge{background:#ff2d55;color:#fff;border-radius:50%;padding:2px 8px;font-size:12px;font-weight:bold}.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#0a0a0a;display:flex;justify-content:space-around;padding:10px 0;border-top:1px solid #222;max-width:600px;margin:auto}.bottom-nav a{color:#888;text-decoration:none;font-size:22px;display:flex;flex-direction:column;align-items:center;gap:2px}.bottom-nav a.active{color:#1a73e8}.bottom-nav .label{font-size:10px}
    </style>
    </head>
    <body>
        <div class=chat-container>
            <div class=top-bar><a href=/feed>‹</a><span class=title>💬 ውይይት</span><span></span></div>
            <div style="padding:10px 20px;color:#888;font-size:14px;">👥 ሰዎችን ይምረጡ</div>
    '''
    for uid, un, ppic in users:
        unread_count = unread.get(uid, 0)
        img_html = f'<img src="/uploads/{ppic}">' if ppic else '👤'
        badge_html = f'<span class="unread-badge">{unread_count}</span>' if unread_count > 0 else ''
        html += f'<a href=/chat/{uid} class=user-item><div class=user-img>{img_html}</div><div class=user-info><div class=name>{un}</div><div class=status>{"📩 አዲስ መልዕክት" if unread_count > 0 else "🟢 ኦንላይን"}</div></div>{badge_html}</a>'
    
    html += f'''
        </div>
        <div class=bottom-nav>
            <a href=/feed>🏠<span class=label>መነሻ</span></a>
            <a href=/search>🔍<span class=label>ፈልግ</span></a>
            <a href=/chat class=active>💬<span class=label>ውይይት</span></a>
            <a href=/premium>👑<span class=label>ፕሪሚየም</span></a>
            <a href=/profile/{session['user_id']}>👤<span class=label>ፕሮፋይል</span></a>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/chat/<int:receiver_id>', methods=['GET', 'POST'])
def chat_user(receiver_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            c.execute("INSERT INTO messages (sender_id, receiver_id, content, timestamp) VALUES (?, ?, ?, ?)",
                      (session['user_id'], receiver_id, content, datetime.now()))
            c.execute("INSERT INTO notifications (user_id, type, from_user_id, timestamp) VALUES (?, ?, ?, ?)",
                      (receiver_id, 'message', session['user_id'], datetime.now()))
            conn.commit()
        conn.close()
        return redirect('/chat/' + str(receiver_id))
    c.execute('''SELECT m.id, m.sender_id, m.content, m.timestamp, u.username, u.profile_pic
                 FROM messages m JOIN users u ON m.sender_id = u.id
                 WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?)
                 ORDER BY m.timestamp ASC''', (session['user_id'], receiver_id, receiver_id, session['user_id']))
    messages = c.fetchall()
    c.execute("UPDATE messages SET is_read=1 WHERE sender_id=? AND receiver_id=?", (receiver_id, session['user_id']))
    conn.commit()
    c.execute("SELECT username, profile_pic FROM users WHERE id=?", (receiver_id,))
    receiver = c.fetchone()
    conn.close()
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>💬 {receiver[0]}</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,Arial,sans-serif;background:#000;color:#fff;height:100vh;display:flex;flex-direction:column}}.chat-container{{max-width:600px;margin:auto;background:#0a0a0a;flex:1;display:flex;flex-direction:column;width:100%}}.top-bar{{padding:12px 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #222;background:#0a0a0a}}.top-bar a{{color:#fff;text-decoration:none;font-size:24px}}.top-bar .title{{font-size:16px;font-weight:bold;flex:1}}.messages{{flex:1;padding:16px;overflow-y:auto;display:flex;flex-direction:column;gap:8px}}.message{{max-width:80%;padding:10px 14px;border-radius:16px;font-size:14px;word-wrap:break-word}}.message.sent{{align-self:flex-end;background:#1a73e8;color:#fff;border-bottom-right-radius:4px}}.message.received{{align-self:flex-start;background:#1a1a1a;color:#fff;border-bottom-left-radius:4px}}.message .time{{font-size:10px;color:#888;margin-top:4px;display:block}}.input-area{{display:flex;padding:12px 16px;border-top:1px solid #222;background:#0a0a0a;gap:8px}}.input-area input{{flex:1;padding:10px 16px;border-radius:25px;border:1px solid #333;background:#1a1a1a;color:#fff;font-size:14px;outline:none}}.input-area input:focus{{border-color:#1a73e8}}.input-area button{{padding:10px 20px;border-radius:25px;border:none;background:#1a73e8;color:#fff;font-weight:bold;cursor:pointer}}.input-area button:hover{{background:#1557b0}}.bottom-nav{{display:none}}
    </style>
    </head>
    <body>
        <div class=chat-container>
            <div class=top-bar><a href=/chat>‹</a><span class=title>💬 {receiver[0]}</span><span></span></div>
            <div class=messages id=messages>
    '''
    for msg in messages:
        mid, sid, cont, ts, un, ppic = msg
        ts_str = ts[:16] if ts else 'አሁን'
        cls = 'sent' if sid == session['user_id'] else 'received'
        html += f'<div class="message {cls}">{cont}<span class="time">{ts_str}</span></div>'
    
    html += f'''
            </div>
            <div class=input-area>
                <form method=post style="display:flex;gap:8px;width:100%;">
                    <input type=text name=content placeholder="መልዕክት ጻፍ..." required>
                    <button type=submit>📤</button>
                </form>
            </div>
        </div>
        <script>
            const messagesDiv = document.getElementById('messages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            setInterval(() => {{ location.reload(); }}, 5000);
        </script>
    </body>
    </html>
    '''
    return html

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('social.db')
    c = conn.cursor()
    c.execute('''SELECT n.id, n.type, n.from_user_id, n.post_id, n.timestamp, u.username, u.profile_pic, n.is_read
                 FROM notifications n JOIN users u ON n.from_user_id = u.id
                 WHERE n.user_id = ? ORDER BY n.id DESC''', (session['user_id'],))
    notifs = c.fetchall()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    html = '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🔔 ማስታወቂያ</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,Arial,sans-serif;background:#000;color:#fff}.container{max-width:600px;margin:auto;background:#0a0a0a;min-height:100vh}.top-bar{padding:16px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #222}.top-bar a{color:#fff;text-decoration:none;font-size:24px}.top-bar .title{font-size:18px;font-weight:bold}.notif-item{display:flex;align-items:center;padding:16px 20px;border-bottom:1px solid #1a1a1a;gap:12px}.notif-item .icon{font-size:24px}.notif-item .text{flex:1}.notif-item .text .username{color:#1a73e8;font-weight:bold}.notif-item .text .time{color:#888;font-size:12px;display:block;margin-top:4px}.notif-item .profile-img{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#e74c3c,#f39c12);display:flex;align-items:center;justify-content:center;font-size:18px;overflow:hidden;flex-shrink:0}.notif-item .profile-img img{width:100%;height:100%;object-fit:cover}.no-notifs{text-align:center;color:#666;padding:60px 20px;font-size:16px}.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#0a0a0a;display:flex;justify-content:space-around;padding:10px 0;border-top:1px solid #222;max-width:600px;margin:auto}.bottom-nav a{color:#888;text-decoration:none;font-size:22px;display:flex;flex-direction:column;align-items:center;gap:2px}.bottom-nav a.active{color:#1a73e8}.bottom-nav .label{font-size:10px}
    </style>
    </head>
    <body>
        <div class=container>
            <div class=top-bar><a href=/feed>‹</a><span class=title>🔔 ማስታወቂያ</span><span></span></div>
    '''
    if notifs:
        for nid, ntype, from_uid, post_id, ts, un, ppic, is_read in notifs:
            ts_str = ts[:16] if ts else 'አሁን'
            img_html = f'<img src="/uploads/{ppic}">' if ppic else '👤'
            if ntype == 'like': icon, text = '❤️', f'<span class=username>{un}</span> ልጥፍህን ወዷል'
            elif ntype == 'comment': icon, text = '💬', f'<span class=username>{un}</span> ልጥፍህ ላይ አስተያየት ሰጥቷል'
            elif ntype == 'follow': icon, text = '➕', f'<span class=username>{un}</span> አንተን ከተለህ'
            elif ntype == 'message': icon, text = '💬', f'<span class=username>{un}</span> መልዕክት ልኮልህ'
            elif ntype == 'donation': icon, text = '🎁', f'<span class=username>{un}</span> ልገሳ ልኮልህ'
            else: icon, text = '🔔', f'<span class=username>{un}</span> አዲስ እንቅስቃሴ'
            html += f'<div class=notif-item><div class=profile-img>{img_html}</div><div class=text><span class=icon>{icon}</span> {text}<span class=time>{ts_str}</span></div></div>'
    else:
        html += '<div class=no-notifs>🔔 ምንም ማስታወቂያ የለም!</div>'
    
    html += f'''
        </div>
        <div class=bottom-nav>
            <a href=/feed>🏠<span class=label>መነሻ</span></a>
            <a href=/search>🔍<span class=label>ፈልግ</span></a>
            <a href=/chat>💬<span class=label>ውይይት</span></a>
            <a href=/premium>👑<span class=label>ፕሪሚየም</span></a>
            <a href=/profile/{session['user_id']} class=active>👤<span class=label>ፕሮፋይል</span></a>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/search', methods=['GET','POST'])
def search():
    if 'user_id' not in session:
        return redirect('/login')
    results = []
    if request.method == 'POST':
        query = request.form.get('query','').strip()
        if query:
            conn = sqlite3.connect('social.db')
            c = conn.cursor()
            c.execute("SELECT id, username, bio FROM users WHERE username LIKE ? OR bio LIKE ?", (f'%{query}%', f'%{query}%'))
            results = c.fetchall()
            conn.close()
    html = '''
    <style>body{font-family:Arial;padding:20px;max-width:600px;margin:auto;background:#0a0a0a;color:#fff}input{width:100%;padding:10px;border-radius:8px;border:1px solid #333;background:#222;color:#fff}button{background:#1a73e8;color:#fff;border:none;padding:10px 20px;border-radius:25px;cursor:pointer}.result{background:#1a1a1a;padding:15px;border-radius:12px;margin-bottom:10px}a{color:#1a73e8;text-decoration:none}
    </style>
    <h2>🔍 ተጠቃሚዎችን ፈልግ</h2>
    <form method=post><input name=query placeholder="ስም ወይም ስለራሳቸው..."><br><br><button type=submit>🔍 ፈልግ</button></form><br>
    '''
    for uid, un, bio in results:
        html += f'<div class=result><a href=/profile/{uid}><b>{un}</b></a><p style=color:#888>{bio or ""}</p></div>'
    
    html += f'<a href=/feed>⬅️ ወደ ቪዲዮዎች</a>'
    html += f'''
    <div class=bottom-nav>
        <a href="/feed">🏠<span class="label">መነሻ</span></a>
        <a href="/search" class="active">🔍<span class="label">ፈልግ</span></a>
        <a href="/chat">💬<span class="label">ውይይት</span></a>
        <a href="/premium">👑<span class="label">ፕሪሚየም</span></a>
        <a href="/profile/{session['user_id']}">👤<span class="label">ፕሮፋይል</span></a>
    </div>
    '''
    return html

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
