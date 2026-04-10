# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Persist school data in a unified JSON datastore
- Automatic migration from legacy `data/activities.json` format
- Repository-style persistence abstraction for safer future changes

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

   You can also run with Uvicorn:

   ```
   uvicorn app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove student from an activity                                  |
| GET    | `/users`                                                          | List persisted student profiles                                     |
| POST   | `/users?email=...&name=...`                                       | Create or update a student profile                                 |
| GET    | `/clubs`                                                          | List persisted clubs                                                |
| GET    | `/memberships`                                                    | List club membership records                                        |
| POST   | `/clubs/{club_id}/memberships?email=...&status=...`              | Create/update membership status                                     |
| GET    | `/event-states`                                                   | List participation intent state (`interested`/`going`)             |
| POST   | `/activities/{activity_name}/states?email=...&state=interested`  | Track per-user event state                                          |

## Data Model

The application uses a JSON-backed repository with these entities:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:

   - Name
   - Grade level

3. **Clubs**

   - Name
   - Description
   - Admin list

4. **Memberships**

   - Club + student relationship
   - Membership status

5. **Event states**

   - `interested` and `going` lists per activity

## Persistence and Migration Strategy

- New canonical file: `data/school_data.json`
- Legacy file supported: `data/activities.json`
- On startup, if `school_data.json` does not exist but `activities.json` does, the app migrates activity data into the new structure and seeds related entities.
- If neither file exists, the app seeds default activities and a default `general` club.

This strategy preserves backward-compatible activity APIs while enabling persistent storage for additional domain entities.
