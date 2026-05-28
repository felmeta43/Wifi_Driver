from .models import HospitalSettings, Notification


def hospital_settings(request):
    settings = HospitalSettings.get_settings()
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    return {
        'hospital': settings,
        'unread_notifications': unread_notifications,
    }
