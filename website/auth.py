# This file routes the user to the homepage or login
from flask import Blueprint, render_template

# Defines blueprint for urls
auth = Blueprint("auth", __name__)

# define a view/root
@auth.route("/login")
def login():
    return render_template("login.html")

@auth.route("/logout")
def logout():
    return "<h1>blehh</h1>"

@auth.route("/sign-up")
def sign_up():
    return render_template("sign_up.html")