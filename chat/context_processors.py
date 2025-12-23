from django.utils.translation import get_language
from .models import UserProfile

def language_processor(request):
    """
    Add language information to template context
    """
    current_language = get_language()
    is_rtl = current_language == 'ar'
    
    return {
        'current_language': current_language,
        'is_rtl': is_rtl,
        'LANGUAGES': [
            ('en', 'English'),
            ('ar', 'العربية'),
        ],
    }

def dark_mode_processor(request):
    """
    Add dark mode preference to template context
    """
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            theme = profile.theme
        except UserProfile.DoesNotExist:
            theme = 'auto'
    else:
        theme = request.session.get('theme', 'auto')
    
    return {
        'theme': theme,
    }