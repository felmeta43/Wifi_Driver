from .models import HospitalSettings, Notification


def hospital_settings(request):
    settings = HospitalSettings.get_settings()
    unread_notifications = 0
    pending_collection_today = False   # cashier: True if today not yet submitted
    pending_approvals = 0              # finance_head: count awaiting approval

    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        role = getattr(request.user, 'role', '')

        if role == 'cashier' or request.user.is_superuser:
            from datetime import date
            from billing.models import DailyCollection
            today_col = DailyCollection.objects.filter(
                cashier=request.user, collection_date=date.today()
            ).first()
            pending_collection_today = (today_col is None or today_col.status == 'draft')

        if role in ('finance_head', 'admin') or request.user.is_superuser:
            from billing.models import DailyCollection
            pending_approvals = DailyCollection.objects.filter(status='submitted').count()

    return {
        'hospital': settings,
        'unread_notifications': unread_notifications,
        'pending_collection_today': pending_collection_today,
        'pending_approvals': pending_approvals,
    }
