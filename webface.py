from flask import Flask, render_template, request, redirect, url_for, session, flash
import functools
from sqlitewrap import SQLite
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import IntegrityError
import datetime

#Podstránky
app = Flask(__name__)
app.secret_key = b"totoj e zceLa n@@@hodny retezec nejlep os.urandom(24)"
app.secret_key = b"x6\x87j@\xd3\x88\x0e8\xe8pM\x13\r\xafa\x8b\xdbp\x8a\x1f\xd41\xb8"

@app.route("/", methods=["GET"])
def home():
    return render_template("base.html")

@app.route("/tymy/")
def tymy():
    return render_template("tymy.html")

@app.route("/tabulka/")
def tabulka():
    return render_template("tabulka.html")

@app.route("/strelci/")
def strelci():
    return render_template("strelci.html")

#vzkazy
@app.route("/vzkazy/", methods=["GET"])
def vzkazy():
    if "user" not in session:
        flash("Tato stánka je pouze pro příhlášené!")
        return redirect(url_for("login", url=request.path))

    with SQLite("data.sqlite") as cursor:
        response = cursor.execute(
            "SELECT login, body, datetime, message.id FROM user JOIN message ON user.id = message.user_id ORDER BY datetime DESC"
        )
        response = response.fetchall()

    return render_template("vzkazy.html", response=response, d=datetime.datetime)

@app.route("/vzkazy/", methods=["POST"])
def vzkazy_post():
    if "user" not in session:
        flash("Tato stánka je pouze pro příhlášené!")
        return redirect(url_for("login", url=request.path))

    with SQLite("data.sqlite") as cursor:
        response = cursor.execute(
            "SELECT id FROM user WHERE login=?", [session["user"]]
        )
        # response = response.fetchone()
        # user_id = list(response)[0]
        user_id = list(response.fetchone())[0]

    vzkaz = request.form.get("body")
    if vzkaz:
        with SQLite("data.sqlite") as cursor:
            cursor.execute(
                "INSERT INTO message (user_id, body, datetime) VALUES (?,?,?)",
                [user_id, vzkaz, datetime.datetime.now()]
            )
    return redirect(url_for("vzkazy"))

@app.route("/vzkazy/del/", methods=["POST"])
def vzkazy_del():
    id = request.form.get("id")
    if id:
        with SQLite("data.sqlite") as cursor:
            response = cursor.execute(
                "SELECT id FROM user WHERE login=?", [session["user"]]
            )
            user_id = response.fetchone()[0]
            cursor.execute(
                "DELETE FROM message WHERE id=? and user_id=?", [id, user_id] 
            )
    return redirect(url_for("vzkazy"))

@app.route("/vzkazy/edit/<int:id>")
def vzkazy_edit(id):
    with SQLite("data.sqlite") as cursor:
        response = cursor.execute("SELECT body FROM message WHERE id=?", [id])
        body = response.fetchone()[0]
    return render_template("vzkazy_edit.html", body=body)


@app.route("/vzkazy/edit/<int:id>", methods=["POST"])
def vzkazy_edit_post(id):
    body = request.form.get("body")
    if body:
        with SQLite("data.sqlite") as cursor:
            cursor.execute(
                "UPDATE message SET body=? WHERE id=? and user_id="
                "(SELECT id FROM user WHERE login=?)", [body, id, session["user"] ]
            )
    return redirect(url_for("vzkazy"))

#login
@app.route("/login/", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login/", methods=["POST"])
def login_post():
    jmeno = request.form.get("jmeno", "")
    heslo = request.form.get("heslo", "")
    url = request.args.get("url", "")  # url je obsažená v adrese. proto request.args

    with SQLite('data.sqlite') as cursor:
        response = cursor.execute(f"SELECT login, passwd FROM user WHERE login = ?", [jmeno])
        response = response.fetchone()

        if response:
            login, passwd = response
            if check_password_hash(passwd, heslo):
                session["user"] = jmeno
                flash("Jsi přihlášen!", "success")
                if url:
                    return redirect(url)
                else:
                    return redirect(url_for("home"))
        
        flash("Nesprávné přihlašovací údaje!", "error")
        return redirect(url_for("login", url=url))

#Logout
@app.route("/logout/")
def logout():
    session.pop("user", None)
    flash("Byl jsi odhlášen!", "success")
    return redirect(url_for("home"))

#Register
@app.route("/register/", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/register/", methods=["POST"])
def register_post():
    jmeno = request.form.get('jmeno', '')
    heslo1 = request.form.get('heslo1', '')
    heslo2 = request.form.get('heslo2', '')

    if len(jmeno) <5:
        flash("Jmeno musí mít alespoň 5 znaků", "error")
        return redirect(url_for("register"))
    if len(heslo1) <5:
        flash("Heslo musí mít alespoň 5 znaků", "error")
        return redirect(url_for("register"))
    if heslo1 != heslo2:
        flash("Zadej dvakrát stejné heslo", "error")
        return redirect(url_for("register"))
        
    hash_ = generate_password_hash(heslo1)
    try:
        with SQLite("data.sqlite") as cursor:
            cursor.execute('INSERT INTO user (login,passwd) VALUES (?,?)', [jmeno, hash_])
        flash(f"Uživatel `{jmeno}` byl přidán!", "success")
    except IntegrityError:
         flash(f"Uživatel `{jmeno}` již existuje!", "error")

    return redirect(url_for("register"))