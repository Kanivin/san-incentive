import threading
from .models import Permission

_thread_locals = threading.local()

def get_current_user():
    """Return the current user stored in thread-local storage."""
    return getattr(_thread_locals, 'user', None)


class ThreadLocalMiddleware:
    """Stores the currently logged-in user in thread-local storage."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user
        response = self.get_response(request)
        return response


class PermissionsMiddleware:
    """Injects the current user's role-based permissions into the request object."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        role_id = request.session.get('role_id')
        if role_id:
            perms = Permission.objects.select_related('module').filter(role_id=role_id)
            request.permissions = {
                (p.module.module, action): getattr(p, f"can_{action}")
                for p in perms
                if p.module  # safeguard against missing module
                for action in ['view', 'add', 'edit', 'delete']
            }
        else:
            request.permissions = {}
        return self.get_response(request)
        
def clear_modal_flag_middleware(get_response):
    def middleware(request):
        response = get_response(request)
        if 'show_modal' in request.session:
            del request.session['show_modal']
        return response
    return middleware