"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import copy
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Persisted activity database
data_dir = current_dir / "data"

default_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


class JsonRepository:
    """Tiny JSON repository abstraction to isolate file persistence concerns."""

    def __init__(self, file_path: Path, default_data: dict[str, Any]):
        self.file_path = file_path
        self.default_data = default_data

    def load(self) -> dict[str, Any]:
        if self.file_path.exists():
            with self.file_path.open("r", encoding="utf-8") as file_handle:
                return json.load(file_handle)

        self.save(copy.deepcopy(self.default_data))
        return copy.deepcopy(self.default_data)

    def save(self, data: dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, sort_keys=True)


class SchoolDataStore:
    """Coordinates persistence and migration for all school domain entities."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.legacy_activities_file = base_dir / "activities.json"
        self.repository = JsonRepository(
            base_dir / "school_data.json",
            self._build_default_data(default_activities)
        )

    def _build_default_data(self, activities: dict[str, Any]) -> dict[str, Any]:
        users: dict[str, Any] = {}
        for participants in activities.values():
            for email in participants.get("participants", []):
                users[email] = {
                    "email": email,
                    "name": "",
                    "grade": None,
                    "phone": None,
                    "preferences": {}
                }

        return {
            "activities": copy.deepcopy(activities),
            "users": users,
            "clubs": {
                "general": {
                    "id": "general",
                    "name": "General Activities Club",
                    "description": "Default club owner for migrated activities",
                    "admins": []
                }
            },
            "memberships": [],
            "event_states": {
                activity_name: {
                    "interested": [],
                    "going": []
                }
                for activity_name in activities
            }
        }

    def load(self) -> dict[str, Any]:
        if self.repository.file_path.exists():
            return self.repository.load()

        if self.legacy_activities_file.exists():
            with self.legacy_activities_file.open("r", encoding="utf-8") as file_handle:
                legacy_activities = json.load(file_handle)
            migrated_data = self._build_default_data(legacy_activities)
            self.repository.save(migrated_data)
            return migrated_data

        return self.repository.load()

    def save(self, data: dict[str, Any]) -> None:
        self.repository.save(data)


store = SchoolDataStore(data_dir)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return store.load()["activities"]


@app.get("/users")
def get_users():
    return store.load()["users"]


@app.post("/users")
def upsert_user(email: str, name: str = "", grade: str | None = None,
                phone: str | None = None):
    data = store.load()
    data["users"][email] = {
        "email": email,
        "name": name,
        "grade": grade,
        "phone": phone,
        "preferences": data["users"].get(email, {}).get("preferences", {})
    }
    store.save(data)
    return data["users"][email]


@app.get("/clubs")
def get_clubs():
    return store.load()["clubs"]


@app.get("/memberships")
def get_memberships():
    return store.load()["memberships"]


@app.post("/clubs/{club_id}/memberships")
def upsert_membership(club_id: str, email: str, status: str = "pending"):
    data = store.load()

    if club_id not in data["clubs"]:
        raise HTTPException(status_code=404, detail="Club not found")

    if email not in data["users"]:
        data["users"][email] = {
            "email": email,
            "name": "",
            "grade": None,
            "phone": None,
            "preferences": {}
        }

    for membership in data["memberships"]:
        if membership["club_id"] == club_id and membership["email"] == email:
            membership["status"] = status
            store.save(data)
            return membership

    membership = {
        "club_id": club_id,
        "email": email,
        "status": status
    }
    data["memberships"].append(membership)
    store.save(data)
    return membership


@app.get("/event-states")
def get_event_states():
    return store.load()["event_states"]


@app.post("/activities/{activity_name}/states")
def add_activity_state(activity_name: str, email: str, state: str):
    data = store.load()

    if activity_name not in data["activities"]:
        raise HTTPException(status_code=404, detail="Activity not found")

    if state not in {"interested", "going"}:
        raise HTTPException(status_code=400, detail="State must be 'interested' or 'going'")

    data["event_states"].setdefault(activity_name, {"interested": [], "going": []})
    if email not in data["event_states"][activity_name][state]:
        data["event_states"][activity_name][state].append(email)

    if email not in data["users"]:
        data["users"][email] = {
            "email": email,
            "name": "",
            "grade": None,
            "phone": None,
            "preferences": {}
        }

    store.save(data)
    return data["event_states"][activity_name]


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    data = store.load()
    activities = data["activities"]

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)

    if email not in data["users"]:
        data["users"][email] = {
            "email": email,
            "name": "",
            "grade": None,
            "phone": None,
            "preferences": {}
        }

    store.save(data)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    data = store.load()
    activities = data["activities"]

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    store.save(data)
    return {"message": f"Unregistered {email} from {activity_name}"}
