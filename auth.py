from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_conn, fetch_all

bp = Blueprint("auth", __name__)

@bp.get("/login")
def login_form():
    return render_template("login.html")

@bp.post("/login")
def login_post():
    email = request.form.get("email","").strip()
    password = request.form.get("password","").strip()
    with get_conn() as conn:
        rows = fetch_all(conn, """
            SELECT User_ID, Fname, Lname, Email, Role
            FROM User
            WHERE Email = :email AND Password = :password
        """, {"email": email, "password": password})
    if not rows:
        flash("Invalid email or password", "danger")
        return redirect(url_for("auth.login_form"))
    user = rows[0]
    session["user_id"] = user["User_ID"]
    session["user_name"] = f"{user['Fname']} {user['Lname']}"
    session["role"] = user["Role"]
    flash(f"Welcome, {session['user_name']}!", "success")
    return redirect(url_for("main.dashboard"))

@bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login_form"))
