# SkillSwap
# SkillSwap: Campus Skill Exchange & Learning Partner Platform

SkillSwap is a Django + Bootstrap 5 platform where campus communities can exchange skills, post learning requests, and form learning partnerships.

## Features
- Authentication (register, login, logout)
- Profiles with bio, availability, preferred mode, and location
- Skill offers and wants with levels
- Learning requests linked to skills
- Match invitations with accept/reject/completed status
- Explore requests and users with search/filter

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```
5. Start the server:
   ```bash
   python manage.py runserver
   ```

## Running Tests
```bash
python manage.py test
```

## Basic Usage Flow
1. Register and log in.
2. Update your profile with availability and learning preferences.
3. Add skills you can offer and skills you want to learn.
4. Create a learning request tied to a skill.
5. Explore requests or users and send match invitations.
6. Accept, reject, or complete matches from your dashboard.

## Demo Screenshot Notes
- Landing page with academic hero and preview cards.
- Dashboard overview showing skills, requests, and match status badges.
- Explore pages with filters for requests and users.