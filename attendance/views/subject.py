from django.http import JsonResponse
from ..models import Subject

def get_subjects(request):
    """Get list of subjects for the subject dropdown"""
    subjects = Subject.objects.all().values('id', 'code', 'name')
    return JsonResponse({
        'status': 'success',
        'subjects': list(subjects)
    })