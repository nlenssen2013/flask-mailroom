import os
import base64

from flask import Flask, render_template, request, redirect, url_for, session
from passlib.hash import pbkdf2_sha256

from model import Donation, Donor, User

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY").encode()

@app.route('/')
def home():
    return redirect(url_for('all'))

@app.route('/donations/')
def all():
    donations = Donation.select()
    return render_template('donations.jinja2', donations=donations)

@app.route("/create/", methods=["GET", "POST"])
def create():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]

        if name is None or name.isspace() or name == "":
            msg = "Donor cannot be empty or whitespace."
            return render_template("create.jinja2", error=msg)

        try:
            donor = Donor.select().where(Donor.name == name).get()
        except Donor.DoesNotExist:
            donor = Donor(name=request.form["name"])
            donor.save()
        
        try:
            donation = int(request.form["donation"])

            if donation <= 0:
                raise ValueError()

            donation = Donation(donor=donor, value=donation)
            donation.save()
        except ValueError:
            msg = "Donation must be a non-negative number greater than 0"
            return render_template("create.jinja2", error=msg)
        
        if request.form["save"] == "Save Donation":
            return redirect(url_for("all"))

    return render_template("create.jinja2")

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = User.select().where(User.name == request.form["name"]).get()
        except User.DoesNotExist:
            user = None

        if user and pbkdf2_sha256.verify(request.form["password"],
                                         user.password):
            session["username"] = request.form["name"]
        else:
            return render_template("login.jinja2",
                                   error="Invalid username or password.")

        if "redirect_to" in session:
            redirect_to = session.pop("redirect_to")
            return redirect(url_for(redirect_to))
            
        return redirect(url_for("create"))

    return render_template("login.jinja2")

@app.route("/logout/")
def logout():
    if "username" not in session:
        session["redirect_to"] = "all"
        return redirect(url_for("login"))
    
    session.pop("username", None)
    return redirect(url_for("all"))

@app.route("/query/", methods=["GET", "POST"])
def query():
    if request.method == "POST":
        name = request.form["name"]
        try:
            donor = Donor.select().where(Donor.name == name).get()
        except Donor.DoesNotExist:
            msg = f"No such donor named: {name}"
            return render_template("query.jinja2", error=msg)

        donations = Donation.select().join(Donor).where(Donor.name == donor.name)
        total = sum([donation.value for donation in donations])
        return render_template("query.jinja2",
                               donor=donor,
                               donations=donations,
                               total=total)
    
    return render_template("query.jinja2")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
