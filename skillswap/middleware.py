from django.utils import timezone


class ActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            profile = request.user.profile
            now = timezone.now()
            if profile.last_active is None or (now - profile.last_active).total_seconds() > 60:
                profile.last_active = now
                profile.last_path = request.path
                profile.save(update_fields=['last_active', 'last_path'])
        return response