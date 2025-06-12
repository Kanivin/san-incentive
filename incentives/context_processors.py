from .models import UserProfile

def user_profile_context(request):
    user_id = request.session.get('user_id')
    profile = None
    if user_id:
        profile = UserProfile.objects.filter(id=user_id).first()
    return {'user_profile': profile}
