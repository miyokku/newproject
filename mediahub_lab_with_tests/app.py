
import os, sqlite3, time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "lab-secret"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "mediahub.sqlite3")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

ALLOWED = {"jpg","jpeg","png","webp","gif"}
MAX_MB = 5

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, user TEXT, text TEXT, media TEXT)")
    conn.commit(); conn.close()

def allowed_file(name):
    return "." in name and name.rsplit(".",1)[1].lower() in ALLOWED

@app.route("/")
def index():
    conn=db(); posts=conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall(); conn.close()
    return render_template("index.html", posts=posts, user=session.get("user"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"]; p=request.form["password"]
        conn=db()
        try:
            conn.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
            conn.commit()
            flash("Registered")
            return redirect(url_for("login"))
        except:
            flash("User exists")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]; p=request.form["password"]
        conn=db()
        row=conn.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
        conn.close()
        if row:
            session["user"]=u
            return redirect(url_for("index"))
        flash("Wrong credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/post/new", methods=["GET","POST"])
def new_post():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        text=request.form.get("text","")
        file=request.files.get("media")
        filename=None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Unsupported format")
                return redirect(url_for("new_post"))
            file.seek(0,2)
            size=file.tell()/(1024*1024)
            file.seek(0)
            if size>MAX_MB:
                flash("File too large")
                return redirect(url_for("new_post"))
            filename=str(int(time.time()))+"_"+secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_DIR,filename))
        conn=db()
        conn.execute("INSERT INTO posts(user,text,media) VALUES(?,?,?)",(session["user"],text,filename))
        conn.commit(); conn.close()
        return redirect(url_for("index"))
    return render_template("new_post.html")

@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_DIR,filename)

@app.route("/post/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = db()

    # ВАЖНО: fetchone(), а не fetchall()
    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?",
        (post_id,)
    ).fetchone()

    if not post:
        conn.close()
        flash("Post not found")
        return redirect(url_for("index"))

    # Если row_factory настроен, post["user"] будет работать
    if post["user"] != session["user"]:
        conn.close()
        flash("You cannot delete  чужой пост")
        return redirect(url_for("index"))

    if post["media"]:
        file_path = os.path.join(UPLOAD_DIR, post["media"])
        if os.path.exists(file_path):
            os.remove(file_path)

    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    flash("Post deleted")
    return redirect(url_for("index"))

@app.route("/api/slow")
def slow():
    time.sleep(3)
    return jsonify({"status":"ok","delay":3})

if __name__=="__main__":
    init()
    app.run(host="0.0.0.0", port=5000, debug=True)