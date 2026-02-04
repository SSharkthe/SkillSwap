# SkillSwap

# SkillSwap: Campus Skill Exchange & Learning Partner Platform

SkillSwap is a Django + Bootstrap 5 platform where campus communities can exchange skills, post learning requests, and
form learning partnerships.

## Features

- Authentication (register, login, logout)
- Password management (change password at `/accounts/password/change/`)
- Profiles with bio, availability, preferred mode, and location
- Profile avatars (upload images to personalize your account)
- Skill offers and wants with levels
- Recommended partners based on matching wants/offers
- Learning requests linked to skills
- Bookmarked requests saved under "My Bookmarks"
- Notifications for match invitations and status updates
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

## Media Uploads (Avatars)

Uploaded avatars are stored in the `media/` folder when running locally.
Make sure `MEDIA_URL` and `MEDIA_ROOT` are configured (already set in `config/settings.py`).
When `DEBUG=True`, Django serves media files automatically.

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
7. Bookmark requests to keep a personalized list at `/bookmarks/`.
8. Review personalized recommendations at `/recommendations/` and notifications at `/notifications/`.
4. Review recommended partners based on your wants.
5. Create a learning request tied to a skill.
6. Explore requests or users and send match invitations.
7. Accept, reject, or complete matches from your dashboard.
8. Leave feedback after a match is completed.

## Recommendations & Feedback

- Recommendations are computed by comparing your "want" skills with other users' "offer" skills.
  Users are ranked by overlap score (want/offer overlap plus mutual overlap).
- Feedback can be left only after a match is marked completed, once per participant.
  Ratings are shown on profile pages along with recent comments.

## Notifications

- Match invites and status changes (accepted/rejected/completed) trigger notifications for the relevant users.
- Visit `/notifications/` to review them and mark items as read.

## Activity Tracking

- A custom middleware updates `last_active` and `last_path` on profiles for authenticated users.
- Updates are throttled to once per 60 seconds to reduce database writes.

## Demo Screenshot Notes

- Landing page with academic hero and preview cards.
- Dashboard overview showing skills, requests, and match status badges.
- Explore pages with filters for requests and users.