from django.utils import timezone


class ActivityMiddleware:
    # Save the next middleware or view function
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # First process the request and get the response
        response = self.get_response(request)

        # Only track activity for logged-in users
        if request.user.is_authenticated:
            profile = request.user.profile
            now = timezone.now()

            # Update activity info if it has not been updated recently
            if profile.last_active is None or (now - profile.last_active).total_seconds() > 60:
                profile.last_active = now
                # Store the last visited path
                profile.last_path = request.path
                profile.save(update_fields=['last_active', 'last_path'])

        return response