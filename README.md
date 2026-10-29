# 🎟️ CampusRSVP: Event RSVP Platform for College Students

A Flask + SQLite web app where students discover campus events and RSVP in seconds, and organizers manage events and attendees.
Built as a mini-project (Experiment 13, all COs).

![Home page](screenshots/01_home_light.png)

## Features
- Event discovery: search, category filter chips, live "spots left" progress bars, stats strip
- Event page: countdown timer, attendee avatars, RSVP form (client + server validation), duplicate prevention, capacity limit
- My RSVPs: look up by email, change to Going/Maybe, or cancel
- Add to Calendar (`.ics` download)
- Organizer dashboard (password protected): create/delete events, view attendees, export CSV
- JSON API: `/api/events`, `/api/events/<id>/rsvps`
- Dark/light mode, toast notifications, responsive layout, custom 404 page
- 6 pytest tests (RSVP creation, duplicates, capacity, validation, admin auth, 404)

## Tech stack
Python 3 · Flask · Flask-SQLAlchemy (SQLite) · Jinja2 · HTML/CSS/vanilla JS · pytest · Playwright (for screenshots)

## Run locally
```bash
pip install -r requirements.txt
python app.py            # seeds sample data on first run, serves http://127.0.0.1:5000
python -m pytest -q      # run tests
```
Organizer login: `/admin`, default password `admin123` (override with the `ADMIN_PASSWORD` environment variable).

Google Colab / Jupyter: open `run_in_colab.ipynb`.

## Project structure
```
app.py          Flask app factory, models, routes
seed.py         sample events + RSVPs
templates/      Jinja2 pages
static/         CSS + JS
tests/          pytest suite
REPORT.md       assignment report with screenshots
```
