# SkillSwap

# SkillSwap: Campus Skill Exchange & Learning Partner Platform

SkillSwap is a Django + Bootstrap 5 platform where campus communities can exchange skills, post learning requests, and
form learning partnerships.

## Features

- Authentication (register, login, logout)
- Profiles with bio, availability, preferred mode, and location
- Skill offers and wants with levels
- Recommended partners based on matching wants/offers
- Learning requests linked to skills
- Match invitations with accept/reject/completed status
- Post-match ratings and feedback between participants
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
4. Review recommended partners based on your wants.
5. Create a learning request tied to a skill.
6. Explore requests or users and send match invitations.
7. Accept, reject, or complete matches from your dashboard.
8. Leave feedback after a match is completed.

## Recommendations & Feedback

- Recommendations are computed by comparing your "want" skills with other users' "offer" skills.
  Users are ranked by the number of overlapping skills, then by profile completeness and username.
- Feedback can be left only after a match is marked completed, once per participant.
  Ratings are shown on profile pages along with recent comments.

## Demo Screenshot Notes

- Landing page with academic hero and preview cards.
- Dashboard overview showing skills, requests, and match status badges.
- Explore pages with filters for requests and users.
- Explore pages with filters for requests and users.