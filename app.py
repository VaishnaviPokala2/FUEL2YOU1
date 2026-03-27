from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("fuel2you.db")
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, password TEXT, role TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        fuel_type TEXT,
        quantity REAL,
        price REAL,
        total REAL,
        payment TEXT,
        address TEXT,
        status TEXT,
        emergency INTEGER,
        timestamp TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS fuel_price(
        id INTEGER PRIMARY KEY,
        petrol REAL,
        diesel REAL
    )''')

    cur.execute("INSERT OR IGNORE INTO fuel_price VALUES (1,100,90)")
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("fuel2you.db")
        cur = conn.cursor()

        cur.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    (request.form["name"], request.form["email"],
                     request.form["password"], request.form["role"]))

        conn.commit()
        conn.close()
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = sqlite3.connect("fuel2you.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                    (request.form["email"], request.form["password"]))
        user = cur.fetchone()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[4]

            if user[4] == "admin":
                return redirect("/admin")
            elif user[4] == "agent":
                return redirect("/agent")
            else:
                return redirect("/dashboard")

    return render_template("login.html")

# ---------------- USER DASHBOARD ----------------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    conn = sqlite3.connect("fuel2you.db")
    cur = conn.cursor()

    cur.execute("SELECT petrol, diesel FROM fuel_price WHERE id=1")
    petrol, diesel = cur.fetchone()

    if request.method == "POST":
        fuel = request.form["fuel"]
        qty = float(request.form["quantity"])
        payment = request.form["payment"]
        address = request.form["address"]
        emergency = 1 if request.form.get("emergency") else 0

        price = petrol if fuel == "Petrol" else diesel
        total = qty * price

        status = "🚨 Emergency Priority" if emergency else "Pending"

        cur.execute("""INSERT INTO orders(user_id,fuel_type,quantity,price,total,
                    payment,address,status,emergency,timestamp)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (session["user_id"], fuel, qty, price, total,
                     payment, address, status, emergency, str(datetime.now())))

        conn.commit()

        if emergency:
            print("🚨 EMERGENCY ALERT SENT")
            print("Location:", address)

        conn.close()
        return redirect("/receipt")

    conn.close()
    return render_template("dashboard.html", petrol=petrol, diesel=diesel)

# ---------------- RECEIPT ----------------
@app.route("/receipt")
def receipt():
    conn = sqlite3.connect("fuel2you.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 1")
    order = cur.fetchone()

    conn.close()
    return render_template("receipt.html", order=order)

# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET","POST"])
def admin():
    conn = sqlite3.connect("fuel2you.db")
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("UPDATE fuel_price SET petrol=?, diesel=? WHERE id=1",
                    (request.form["petrol"], request.form["diesel"]))
        conn.commit()

    cur.execute("SELECT * FROM orders ORDER BY emergency DESC, id DESC")
    orders = cur.fetchall()

    conn.close()
    return render_template("admin.html", orders=orders)

# ---------------- AGENT ----------------
@app.route("/agent", methods=["GET","POST"])
def agent():
    conn = sqlite3.connect("fuel2you.db")
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("UPDATE orders SET status=? WHERE id=?",
                    (request.form["status"], request.form["order_id"]))
        conn.commit()

    cur.execute("SELECT * FROM orders ORDER BY emergency DESC, id DESC")
    orders = cur.fetchall()

    conn.close()
    return render_template("agent.html", orders=orders)

# ---------------- TRACKING ----------------
@app.route("/tracking")
def tracking():
    return render_template("tracking.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)