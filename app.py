from flask import Flask, request, redirect, send_from_directory, send_file
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, zipfile
import re
STYLE_DATA = {"bg":"", "radius":""}
app = Flask(__name__)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
app.secret_key = "portfolio_secret_key"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads/images")
RESUME_FOLDER = os.path.join(BASE_DIR, "uploads/resumes")
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")

TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
conn = get_db()
conn.execute(
    """CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    domain TEXT,
    about TEXT,
    skills TEXT,
    projects TEXT,
    college_name TEXT,
    cgpa TEXT,
    school_name TEXT,
    percentage TEXT,
    email TEXT,
    github_url TEXT,
    linkedin_url TEXT,
    image TEXT,
    resume TEXT,
    theme TEXT
)""")
conn.commit()
conn.close()
conn = get_db()
conn.execute(
    """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT
)""")
conn.commit()
conn.close()
conn = get_db()
conn.execute("""
CREATE TABLE IF NOT EXISTS recruiters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT,
    password TEXT
)
""")
conn.commit()
conn.close()
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            msg = "Invalid admin credentials"
    html = open("templates/admin_login.html", encoding="utf-8").read()
    return html.replace("{{msg}}", msg)
@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    users = conn.execute("SELECT id, username, email FROM users").fetchall()
    portfolios = conn.execute("SELECT id, name, email FROM portfolio").fetchall()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    portfolio_count = conn.execute("SELECT COUNT(*) FROM portfolio").fetchone()[0]
    conn.close()

    html = open(os.path.join(TEMPLATE_FOLDER, "admin_dashboard.html"), encoding="utf-8").read()

    # ---- USERS TABLE ----
    user_rows = ""
    for u in users:
        user_rows += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{u['username']}</td>
            <td>{u['email']}</td>
            <td>
                <a href="/admin/delete_user/{u['id']}"
                   class="delete-btn"
                   onclick="return confirm('Are you sure you want to delete this user?')">
                   Delete
                </a>
            </td>
        </tr>
        """

    # ---- PORTFOLIOS TABLE ----
    portfolio_rows = ""
    for p in portfolios:
        portfolio_rows += f"""
        <tr>
            <td>{p['id']}</td>
            <td>{p['name']}</td>
            <td>{p['email']}</td>
            <td>
                <a href="/portfolio" target="_blank">View</a>
            </td>
        </tr>
        """

    return (
        html.replace("{{users}}", user_rows)
            .replace("{{portfolios}}", portfolio_rows)
            .replace("{{user_count}}", str(user_count))
            .replace("{{portfolio_count}}", str(portfolio_count))
    )
@app.route("/admin/clear_users")
def admin_clear_users():
    if "admin" not in session:
        return redirect("/admin")
    conn = get_db()
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    return redirect("/admin/dashboard")
@app.route("/admin/clear_portfolios")
def admin_clear_portfolios():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    conn.execute("DELETE FROM portfolio")
    conn.commit()
    conn.close()
    return redirect("/admin/dashboard")
@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")
@app.route("/recruiter/register", methods=["GET","POST"])
def recruiter_register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO recruiters (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            conn.close()
            return redirect("/recruiter/login")
        except:
            conn.close()
            return "Recruiter already exists ❌"

    return open("recruiter_register.html").read()
@app.route("/recruiter/login", methods=["GET","POST"])
def recruiter_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM recruiters WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            return redirect("/recruiter/dashboard")
        else:
            return "Invalid Recruiter Credentials ❌"

    return open("recruiter_login.html").read()
@app.route("/recruiter/dashboard")
def recruiter_dashboard():
    return open("templates/recruiter.html").read()
@app.route("/explore")
def explore():
    conn = get_db()
    portfolios = conn.execute("SELECT * FROM portfolio").fetchall()
    conn.close()

    html = open("templates/explore.html", encoding="utf-8").read()

    cards = ""

    for p in portfolios:
        cards += f"""
        <div class="card" data-domain="{p['domain'].lower()}">
            <img src="/uploads/{p['image']}" class="profile-img">

            <h3>{p['name']}</h3>
            <p class="domain">{p['domain']}</p>

            <p class="skills">{p['skills']}</p>

            <div class="btn-group">
                <a href="/portfolio" target="_blank" class="view-btn">View</a>
                <a href="/resumes/{p['resume']}" download class="download-btn">Resume</a>
            </div>
        </div>
        """

    return html.replace("{{cards}}", cards)

@app.route("/login", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
def auth():

    msg = request.args.get("msg", "")

    if request.method == "POST":

        # If email field exists → REGISTER
        if "email" in request.form:
            username = request.form["username"]
            email = request.form["email"]
            password = generate_password_hash(request.form["password"])

            try:
                conn = get_db()
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, password)
                )
                conn.commit()
                conn.close()
                return redirect("/login?msg=registered")
            except:
                msg = "User already exists."

        # Otherwise → LOGIN
        else:
            username = request.form["username"]
            password = request.form["password"]

            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            ).fetchone()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user"] = username
                return redirect("/index")
            else:
                msg = "Invalid username or password"

    html = open("templates/auth.html", encoding="utf-8").read()
    return html.replace("{{msg}}", msg)
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        new_password = generate_password_hash(request.form["password"])

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if user:
            conn.execute(
                "UPDATE users SET password=? WHERE username=?",
                (new_password, username)
            )
            conn.commit()
            conn.close()
            return redirect("/login?msg=reset")
        else:
            msg = "User not found"

    html = open("forgot.html", encoding="utf-8").read()
    return html.replace("{{msg}}", msg)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------- FILE SERVING ----------
@app.route("/uploads/<filename>")
def uploaded_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/resumes/<filename>")
def uploaded_resume(filename):
    return send_from_directory(RESUME_FOLDER, filename)

# ---------- FORM ----------
@app.route("/")
def role_page():
    return open("templates/role.html", encoding="utf-8").read()

@app.route("/recruiter")
def recruiter():
    return open("templates/recruiter.html", encoding="utf-8").read()

@app.route("/index", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        # save form temporarily
        session["form_data"] = dict(request.form)

        # save files temporarily
        image = request.files["image"]
        resume = request.files["resume"]

        image_path = os.path.join(UPLOAD_FOLDER, image.filename)
        resume_path = os.path.join(RESUME_FOLDER, resume.filename)

        image.save(image_path)
        resume.save(resume_path)

        session["image"] = image.filename
        session["resume"] = resume.filename

        # 👉 go to layout selection page
        return redirect("/choose_layout")

    return open("templates/index.html", encoding="utf-8").read()

@app.route("/choose_layout")
def choose_layout():
    return open("templates/layout.html", encoding="utf-8").read()

@app.route("/save_layout/<layout>")
def save_layout(layout):

    data = session.get("form_data")

    if not data:
        return redirect("/")

    conn = get_db()

    conn.execute("""
    INSERT INTO portfolio (name, domain, about, skills, projects,
    college_name, cgpa, school_name, percentage, email,
    github_url, linkedin_url, image, resume, theme)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["domain"],
        data["about"],
        data["skills"],
        data["projects"],
        data["college_name"],
        data["cgpa"],
        data["school_name"],
        data["percentage"],
        data["email"],
        data["github_url"],
        data["linkedin_url"],
        session.get("image"),
        session.get("resume"),
        layout   # ⭐ IMPORTANT: layout = theme
    ))

    conn.commit()
    conn.close()

    return redirect("/portfolio")

# ---------- PORTFOLIO ----------
@app.route("/portfolio")
def portfolio():
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM portfolio ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    layout = p["theme"]   # using theme column as layout

    # 🔥 LOAD BASED ON LAYOUT
    if layout == "sidebar":
        html = open("templates/layout_sidebar.html", encoding="utf-8").read()

    elif layout == "split":
        html = open("templates/layout_split.html", encoding="utf-8").read()

    elif layout == "modern":
        html = open("templates/layout_modern.html", encoding="utf-8").read()

    else:
        html = open("templates/layout_classic.html", encoding="utf-8").read()

    # 🔥 Inject dynamic data
    return (
        html.replace("{{name}}", str(p["name"]))
            .replace("{{domain}}", str(p["domain"]))
            .replace("{{about}}", str(p["about"]))
            .replace("{{skills}}", str(p["skills"]))
            .replace("{{projects}}", str(p["projects"]))
            .replace("{{college_name}}", str(p["college_name"]))
            .replace("{{cgpa}}", str(p["cgpa"] or "Not Provided"))
            .replace("{{school_name}}", str(p["school_name"]))
            .replace("{{percentage}}", str(p["percentage"]))
            .replace("{{email}}", str(p["email"]))
            .replace("{{github_url}}", str(p["github_url"]))
            .replace("{{linkedin_url}}", str(p["linkedin_url"]))
            .replace("{{image}}", str(p["image"]))
            .replace("{{resume}}", str(p["resume"]))
    )

# ---------- SOURCE CODE DOWNLOAD ----------
@app.route("/download_source")
def download_source():
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM portfolio ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    layout = p["theme"]   # layout stored here

    # 🔥 Load correct layout file
    if layout == "sidebar":
        template = open("layout_sidebar.html", encoding="utf-8").read()

    elif layout == "split":
        template = open("layout_split.html", encoding="utf-8").read()

    elif layout == "modern":
        template = open("templates/layout_modern.html", encoding="utf-8").read()

    else:
        template = open("layout_classic.html", encoding="utf-8").read()

    # 🔥 Inject dynamic data
    html_content = (
        template.replace("{{name}}", str(p["name"]))
        .replace("{{domain}}", str(p["domain"]))
        .replace("{{about}}", str(p["about"]))
        .replace("{{skills}}", str(p["skills"]))
        .replace("{{projects}}", str(p["projects"]))
        .replace("{{college_name}}", str(p["college_name"]))
        .replace("{{cgpa}}", str(p["cgpa"]))
        .replace("{{school_name}}", str(p["school_name"]))
        .replace("{{percentage}}", str(p["percentage"]))
        .replace("{{email}}", str(p["email"]))
        .replace("{{github_url}}", str(p["github_url"]))
        .replace("{{linkedin_url}}", str(p["linkedin_url"]))
        .replace("{{image}}", str(p["image"]))
        .replace("{{resume}}", str(p["resume"]))
    )

    html_content = template

    for key in p.keys():
        html_content = html_content.replace(f"{{{{{key}}}}}", str(p[key] or ""))

    # 🔥 REMOVE EVERYTHING BETWEEN MARKERS
    while "<!-- NO_EXPORT_START -->" in html_content:
        start = html_content.find("<!-- NO_EXPORT_START -->")
        end = html_content.find("<!-- NO_EXPORT_END -->") + len("<!-- NO_EXPORT_END -->")
        html_content = html_content[:start] + html_content[end:]

    # 🔥 Save HTML file
    html_path = os.path.join(EXPORT_FOLDER, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 🔥 Create ZIP
    zip_path = os.path.join(EXPORT_FOLDER, "portfolio_download.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(html_path, "templates/index.html")

        # add assets
        zipf.write(os.path.join(UPLOAD_FOLDER, p["image"]), p["image"])
        zipf.write(os.path.join(RESUME_FOLDER, p["resume"]), p["resume"])

    return send_file(zip_path, as_attachment=True)


@app.route("/save_style")
def save_style():
    STYLE_DATA["bg"] = request.args.get("bg", "")
    STYLE_DATA["radius"] = request.args.get("radius", "")
    return "ok"

# ---------- AI: GENERATE ABOUT ----------
@app.route("/ai_about")
def ai_about():
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM portfolio ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    ai_text = f"""
I am {p['name']}, a passionate software developer with strong skills in {p['skills']}.
I enjoy building web applications and solving real-world problems.
This portfolio showcases my projects, technical abilities, and professional journey.
"""

    return ai_text.strip()


# ---------- AI: GENERATE FULL PORTFOLIO SOURCE ----------
@app.route("/ai_skills")
def ai_skills():
    conn = get_db()
    p = conn.execute(
        "SELECT * FROM portfolio ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    ai_text=f"""
    • Proficient in {p['skills']}<br>
• Strong problem-solving abilities<br>
• Experience in web application development<br>
• Good understanding of modern technologies<br>
• Ability to learn and adapt quickly
"""

    return ai_text.strip()
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
