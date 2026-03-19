from flask import Flask, render_template, request, redirect,session,flash
import sqlite3

app = Flask(__name__)
app.secret_key="super_seccret_key"
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    return render_template("home.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
@app.route("/edit_challenge/<int:id>", methods=["GET","POST"])
def edit_challenge(id):

    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]
        flag = request.form["flag"]
        points = request.form["points"]
        category = request.form["category"]

        db.execute("""
        UPDATE challenges
        SET name=?, description=?, flag=?, points=?, category=?
        WHERE id=?
        """, (name, description, flag, points, category, id))

        db.commit()

        return redirect("/admin")

    challenge = db.execute(
        "SELECT * FROM challenges WHERE id=?",
        (id,)
    ).fetchone()

    return render_template("edit_challenge.html", challenge=challenge)

@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()

    challenges = db.execute("""
    SELECT challenges.*, 
    COUNT(solves.challenge_id) as solves
    FROM challenges
    LEFT JOIN solves
    ON challenges.id = solves.challenge_id
    GROUP BY challenges.id
    """).fetchall()

    return render_template("admin.html", challenges=challenges)
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    db = get_db()

    user = db.execute(
        "SELECT username, score FROM users WHERE id=?",
        (session["id"],)
    ).fetchone()

    solved = db.execute("""
    SELECT challenges.name, challenges.points
    FROM solves
    JOIN challenges
    ON solves.challenge_id = challenges.id
    WHERE solves.user_id=?
    """,(session["id"],)).fetchall()

    return render_template(
        "profile.html",
        user=user,
        solved=solved
    )
@app.route("/add_challenge", methods=["POST"])
def add_challenge():

    if session.get("role") != "admin":
        return "Access denied"

    name = request.form["name"]
    description = request.form["description"]
    flag = request.form["flag"]
    points = request.form["points"]
    category = request.form["category"]

    db = get_db()

    db.execute(
        "INSERT INTO challenges(name,description,flag,points,category) VALUES(?,?,?,?,?)",
        (name,description,flag,points,category)
    )

    db.commit()

    return redirect("/admin")
@app.route("/delete_challenge/<int:id>")
def delete_challenge(id):

    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()

    # challenge ni olish
    challenge = db.execute(
        "SELECT points FROM challenges WHERE id=?",
        (id,)
    ).fetchone()

    if challenge:

        points = challenge["points"]

        # shu challengeni solve qilgan userlarni olish
        users = db.execute(
            "SELECT user_id FROM solves WHERE challenge_id=?",
            (id,)
        ).fetchall()

        for u in users:
            db.execute(
                "UPDATE users SET score = score - ? WHERE id=?",
                (points, u["user_id"])
            )

    # solves o‘chadi
    db.execute("DELETE FROM solves WHERE challenge_id=?", (id,))

    # challenge o‘chadi
    db.execute("DELETE FROM challenges WHERE id=?", (id,))

    db.commit()

    return redirect("/admin")
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # 🔥 HARDCODED ADMIN
        if username == "azimjon2007" and password == "azimjonhusanov2007":
            session["user"] = username
            session["id"] = 0
            session["role"] = "admin"
            return redirect("/admin")

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()

        if user:
            session["user"] = username
            session["id"] = user["id"]
            session["role"] = user["role"]

            return redirect("/dashboard")

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    category = request.args.get("category")

    db = get_db()

    if category:

        challenges = db.execute("""
        SELECT challenges.*, COUNT(solves.challenge_id) as solves
        FROM challenges
        LEFT JOIN solves
        ON challenges.id = solves.challenge_id
        WHERE category=?
        GROUP BY challenges.id
        """,(category,)).fetchall()

    else:

        challenges = db.execute("""
        SELECT challenges.*, COUNT(solves.challenge_id) as solves
        FROM challenges
        LEFT JOIN solves
        ON challenges.id = solves.challenge_id
        GROUP BY challenges.id
        """).fetchall()

    solved = db.execute(
        "SELECT challenge_id FROM solves WHERE user_id=?",
        (session["id"],)
    ).fetchall()

    solved_ids = [s["challenge_id"] for s in solved]

    return render_template(
        "dashboard.html",
        challenges=challenges,
        solved_ids=solved_ids
    )
@app.route("/submit_flag", methods=["POST"])
def submit_flag():

    if "user" not in session:
        return redirect("/login")

    flag = request.form["flag"]
    challenge_id = int(request.form["challenge_id"])

    db = get_db()

    solved = db.execute(
        "SELECT id FROM solves WHERE user_id=? AND challenge_id=?",
        (session["id"], challenge_id)
    ).fetchone()

    if solved:
        flash("You already solved this challenge!")
        return redirect("/dashboard")

    challenge = db.execute(
        "SELECT * FROM challenges WHERE id=?",
        (challenge_id,)
    ).fetchone()

    if challenge and flag == challenge["flag"]:

        db.execute(
            "INSERT INTO solves(user_id,challenge_id) VALUES(?,?)",
            (session["id"], challenge_id)
        )

        db.execute(
            "UPDATE users SET score = score + ? WHERE id=?",
            (challenge["points"], session["id"])
        )

        db.commit()

        flash("Correct flag! 🎉")

        return redirect("/dashboard")

    flash("Wrong flag ❌")
    return redirect("/dashboard")
@app.route("/scoreboard")
def scoreboard():

    db = get_db()

    users = db.execute(
        "SELECT username,score FROM users ORDER BY score DESC"
    ).fetchall()

    return render_template("scoreboard.html",users=users)
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        db.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username,password)
        )

        db.commit()

        return redirect("/")

    return render_template("register.html")

if __name__=="__main__":
	app.run()
