from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication that exempts API calls from CSRF checks.
    Prevents CSRF Failed errors when the user logs into Django Admin in the same browser.
    """
    def enforce_csrf(self, request):
        return
