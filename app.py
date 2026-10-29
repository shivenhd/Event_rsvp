"""CampusRSVP - Event RSVP platform for college students (Flask + SQLite)."""
import csv
import io
import os
import re
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, Response, abort, flash, jsonify, redirect,
                   render_template, request, session, url_for)
from flask_sqlalchemy import SQLAlchemy

CATEGORIES = ["Tech", "Cultural", "Sports", "Workshop", "Social"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

db = SQLAlchemy()


# ----------------------------------------------------------------- models
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(120), nullable=False)
    organizer = db.Column(db.String(80), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=50)
    rsvps = db.relationship("RSVP", backref="event", cascade="all, delete-orphan")

    @property
    def going_count(self):
        # Only "Going" RSVPs consume a seat; "Maybe" does not.
        return sum(1 for r in self.rsvps if r.status == "Going")

    @property
    def spots_left(self):
        return max(self.capacity - self.going_count, 0)

    @property
    def is_full(self):
        return self.spots_left == 0

    @property
    def fill_percent(self):
        return min(100, round(100 * self.going_count / self.capacity)) if self.capacity else 100

    def to_dict(self):
        return {"id": self.id, "title": self.title, "category": self.category,
                "venue": self.venue, "organizer": self.organizer,
                "starts_at": self.starts_at.isoformat(), "capacity": self.capacity,
                "going": self.going_count, "spots_left": self.spots_left}


class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="Going")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("event_id", "email", name="one_rsvp_per_email"),)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "status": self.status, "created_at": self.created_at.isoformat()}


# ---------------------------------------------------------------- factory
def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "campus.db"),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "admin123"),
    )
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    def admin_required(view):
        @wraps(view)
        def wrapper(*a, **kw):
            if not session.get("admin"):
                return redirect(url_for("admin_login"))
            return view(*a, **kw)
        return wrapper

    @app.template_filter("nice_date")
    def nice_date(d):
        return d.strftime("%a, %d %b %Y · %I:%M %p")

    # ------------------------------------------------------------ public
    @app.route("/")
    def home():
        q = request.args.get("q", "").strip()
        cat = request.args.get("category", "")
        query = Event.query.filter(Event.starts_at >= datetime.now() - timedelta(hours=3))
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(Event.title.ilike(like), Event.venue.ilike(like),
                                        Event.description.ilike(like)))
        if cat in CATEGORIES:
            query = query.filter_by(category=cat)
        events = query.order_by(Event.starts_at).all()
        all_events = Event.query.all()
        total_rsvps = RSVP.query.count()
        popular = max(all_events, key=lambda e: len(e.rsvps), default=None)
        return render_template("home.html", events=events, q=q, cat=cat,
                               categories=CATEGORIES, total_events=len(all_events),
                               total_rsvps=total_rsvps, popular=popular)

    @app.route("/event/<int:event_id>", methods=["GET", "POST"])
    def event_detail(event_id):
        event = db.get_or_404(Event, event_id)
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            status = request.form.get("status", "Going")
            error = None
            if len(name) < 2:
                error = "Please enter your full name."
            elif not EMAIL_RE.match(email):
                error = "Please enter a valid email address."
            elif status not in ("Going", "Maybe"):
                error = "Invalid RSVP status."
            elif RSVP.query.filter_by(event_id=event.id, email=email).first():
                error = "This email has already RSVPed. Use 'My RSVPs' to change it."
            elif status == "Going" and event.is_full:
                error = "Sorry, this event is full. You can still RSVP as Maybe."
            if error:
                flash(error, "error")
                return render_template("event.html", event=event, form=request.form), 400
            db.session.add(RSVP(event_id=event.id, name=name, email=email, status=status))
            db.session.commit()
            flash(f"You're in! RSVP saved as '{status}'.", "success")
            return redirect(url_for("event_detail", event_id=event.id))
        return render_template("event.html", event=event, form={})

    @app.route("/my-rsvps", methods=["GET", "POST"])
    def my_rsvps():
        email = (request.values.get("email") or "").strip().lower()
        rsvps = RSVP.query.filter_by(email=email).all() if email else []
        return render_template("my_rsvps.html", email=email, rsvps=rsvps,
                               searched=bool(email))

    @app.post("/rsvp/<int:rsvp_id>/update")
    def update_rsvp(rsvp_id):
        r = db.get_or_404(RSVP, rsvp_id)
        status = request.form.get("status")
        if status == "cancel":
            db.session.delete(r)
            flash("RSVP cancelled.", "success")
        elif status in ("Going", "Maybe"):
            if status == "Going" and r.status != "Going" and r.event.is_full:
                flash("Event is full, can't switch to Going.", "error")
                return redirect(url_for("my_rsvps", email=r.email))
            r.status = status
            flash(f"RSVP updated to '{status}'.", "success")
        db.session.commit()
        return redirect(url_for("my_rsvps", email=r.email))

    @app.route("/event/<int:event_id>/calendar.ics")
    def calendar(event_id):
        e = db.get_or_404(Event, event_id)
        fmt = "%Y%m%dT%H%M%S"
        ics = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//CampusRSVP//EN\r\nBEGIN:VEVENT\r\n"
               f"UID:event-{e.id}@campusrsvp\r\nDTSTART:{e.starts_at.strftime(fmt)}\r\n"
               f"DTEND:{(e.starts_at + timedelta(hours=2)).strftime(fmt)}\r\n"
               f"SUMMARY:{e.title}\r\nLOCATION:{e.venue}\r\n"
               f"DESCRIPTION:{e.description[:200]}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
        return Response(ics, mimetype="text/calendar",
                        headers={"Content-Disposition": f"attachment; filename=event-{e.id}.ics"})

    # --------------------------------------------------------------- API
    @app.route("/api/events")
    def api_events():
        return jsonify([e.to_dict() for e in Event.query.order_by(Event.starts_at)])

    @app.route("/api/events/<int:event_id>/rsvps")
    def api_rsvps(event_id):
        e = db.get_or_404(Event, event_id)
        return jsonify({"event": e.title, "rsvps": [r.to_dict() for r in e.rsvps]})

    # ------------------------------------------------------------- admin
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            if request.form.get("password") == app.config["ADMIN_PASSWORD"]:
                session["admin"] = True
                return redirect(url_for("admin"))
            flash("Wrong password.", "error")
        return render_template("admin_login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin", None)
        return redirect(url_for("home"))

    @app.route("/admin", methods=["GET", "POST"])
    @admin_required
    def admin():
        if request.method == "POST":
            f = request.form
            try:
                starts = datetime.strptime(f["starts_at"], "%Y-%m-%dT%H:%M")
                cap = int(f["capacity"])
                if cap < 1 or f["category"] not in CATEGORIES or not f["title"].strip():
                    raise ValueError
            except (ValueError, KeyError):
                flash("Please fill all fields correctly.", "error")
                return redirect(url_for("admin"))
            db.session.add(Event(title=f["title"].strip(), category=f["category"],
                                 description=f["description"].strip(), venue=f["venue"].strip(),
                                 organizer=f["organizer"].strip(), starts_at=starts, capacity=cap))
            db.session.commit()
            flash("Event created!", "success")
            return redirect(url_for("admin"))
        events = Event.query.order_by(Event.starts_at).all()
        return render_template("admin.html", events=events, categories=CATEGORIES)

    @app.route("/admin/event/<int:event_id>")
    @admin_required
    def admin_event(event_id):
        return render_template("admin_event.html", event=db.get_or_404(Event, event_id))

    @app.route("/admin/event/<int:event_id>/export.csv")
    @admin_required
    def export_csv(event_id):
        e = db.get_or_404(Event, event_id)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Name", "Email", "Status", "RSVP time"])
        for r in e.rsvps:
            w.writerow([r.name, r.email, r.status, r.created_at.strftime("%Y-%m-%d %H:%M")])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=event-{e.id}-rsvps.csv"})

    @app.post("/admin/event/<int:event_id>/delete")
    @admin_required
    def delete_event(event_id):
        db.session.delete(db.get_or_404(Event, event_id))
        db.session.commit()
        flash("Event deleted.", "success")
        return redirect(url_for("admin"))

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    from seed import seed
    with app.app_context():
        if Event.query.count() == 0:
            seed(db, Event, RSVP)
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
