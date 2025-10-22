from .models import Comment

def pending_comments(request):
    """Add pending comments count to all template contexts"""
    if request.session.get('admin_id'):
        pending_count = Comment.objects.filter(is_approved=False).count()
        return {'pending_comments_count': pending_count}
    return {'pending_comments_count': 0}
