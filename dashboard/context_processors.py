from .models import CloudConnection

def account_context(request):
    if request.user.is_authenticated:
        account = CloudConnection.objects.filter(user=request.user).first()
        return {'account': account}
    return {'account': None}