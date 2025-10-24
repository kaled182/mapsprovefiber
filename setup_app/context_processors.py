from .models import FirstTimeSetup

def setup_logo(request):
    setup = FirstTimeSetup.objects.filter(configured=True).order_by('-configured_at').first()
    return {'setup_logo': setup}
