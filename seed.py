"""Populate the database with realistic sample events and RSVPs."""
import random
from datetime import datetime, timedelta

from app import Event, RSVP, app, db

EVENTS = [
    ("HackSprint 2026: 24-Hour Hackathon", "Tech", "Team up with fellow students to build a working prototype in 24 hours. Mentors from industry, free meals, and prizes for the top three teams. Beginners are welcome.", "Innovation Lab, Block C", "Coding Club", 3, 80),
    ("Intro to Machine Learning Workshop", "Workshop", "A hands-on session covering regression, classification and a first neural network in Python. Bring your laptop; Google Colab is all you need.", "Seminar Hall 2", "AI Society", 5, 40),
    ("Annual Cultural Fest: Rang Tarang", "Cultural", "Dance, music, drama and food stalls across the main quadrangle. Register your department's act or simply come and enjoy the evening.", "Main Quadrangle", "Cultural Committee", 9, 300),
    ("Inter-College Football Tournament", "Sports", "Knockout-format 7-a-side football. Teams of 10 can register at the sports office. Spectators welcome.", "University Ground", "Sports Council", 7, 120),
    ("Resume & LinkedIn Clinic", "Workshop", "Placement cell alumni review your resume one-on-one and share what recruiters actually look for.", "Placement Cell, Room 104", "Placement Cell", 2, 25),
    ("Open Mic Night", "Social", "Poetry, stand-up, songs, anything goes. Sign up at the door for a 5-minute slot or just cheer from the audience.", "Campus Cafe", "Literary Club", 4, 60),
    ("Cloud Computing 101 with AWS", "Tech", "Launch your first EC2 instance, host a static site on S3 and learn the free-tier basics. Certificates for attendees.", "Computer Lab 3", "Cloud Club", 11, 30),
    ("Freshers vs Seniors Quiz Night", "Social", "Pop-culture, tech and general knowledge rounds in mixed teams of four. Snacks included.", "Auditorium", "Quiz Society", 6, 100),
    ("Photography Walk: Old City Heritage", "Cultural", "A guided morning walk through heritage streets with tips on composition and light from the photography club.", "Meet at Main Gate", "Photo Club", 13, 20),
]
NAMES = ["Aarav Mehta", "Diya Shah", "Rohan Iyer", "Sneha Patil", "Kabir Singh", "Ananya Rao",
         "Vihaan Desai", "Isha Nair", "Arjun Kulkarni", "Meera Joshi", "Neel Gupta", "Riya Sharma",
         "Karan Malhotra", "Tanvi Bhat", "Yash Verma", "Pooja Reddy", "Aditya Jain", "Kriti Sen"] + [f"Student {i}" for i in range(1, 30)]


def seed():
    random.seed(7)
    base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    for i, (title, cat, desc, venue, org, days, cap) in enumerate(EVENTS):
        e = Event(title=title, category=cat, description=desc, venue=venue, organizer=org,
                  starts_at=base + timedelta(days=days, hours=random.choice([0, 2, 4, 7])), capacity=cap)
        db.session.add(e)
        db.session.flush()
        # The clinic is intentionally almost full to demo the capacity UI.
        n = cap - 1 if title.startswith("Resume") else random.randint(4, min(len(NAMES), cap))
        for name in random.sample(NAMES, min(n, len(NAMES))):
            db.session.add(RSVP(event_id=e.id, name=name,
                                email=name.lower().replace(" ", ".") + "@college.edu",
                                status="Going" if title.startswith("Resume") else random.choice(["Going", "Going", "Going", "Maybe"])))
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed()
        print("Seeded", Event.query.count(), "events and", RSVP.query.count(), "RSVPs")
