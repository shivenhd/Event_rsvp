import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime, timedelta
import pytest
from app import Event, RSVP, create_app, db


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/t.db"})
    with app.app_context():
        db.session.add(Event(title="Test", category="Tech", description="d", venue="v",
                             organizer="o", starts_at=datetime.now() + timedelta(days=2), capacity=1))
        db.session.commit()
    return app.test_client()


def rsvp(c, email="a@b.edu", status="Going"):
    return c.post("/event/1", data={"name": "Alice", "email": email, "status": status})


def test_rsvp_created(client):
    assert rsvp(client).status_code == 302
    assert client.get("/api/events").json[0]["going"] == 1


def test_duplicate_blocked(client):
    rsvp(client)
    assert rsvp(client).status_code == 400


def test_capacity_enforced(client):
    rsvp(client)
    assert rsvp(client, "x@y.edu").status_code == 400
    assert rsvp(client, "x@y.edu", "Maybe").status_code == 302


def test_invalid_email(client):
    assert rsvp(client, "nope").status_code == 400


def test_admin_requires_login(client):
    assert client.get("/admin").status_code == 302
    client.post("/admin/login", data={"password": "admin123"})
    assert client.get("/admin").status_code == 200


def test_404_page(client):
    assert client.get("/nothing").status_code == 404
