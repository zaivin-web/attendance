from django.shortcuts import render
from django.http import JsonResponse
from ..models import Student
from ..utils import generate_qr_code
import json

def generate_qr(request):
    """View for generating QR codes"""
    if request.method == 'GET':
        return render(request, 'qrgenerator.html')
    
    elif request.method == 'POST':
        try:
            # Get the student from database
            try:
                student = Student.objects.get(lrn=request.POST.get('lrn'))
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Student not found'
                })
            
            # Generate QR code with student data
            qr_data = {
                'name': f"{student.first_name} {student.last_name}",
                'lrn': student.lrn,
                'section': student.section,
                'student_id': student.student_id
            }
            
            qr_code = generate_qr_code(json.dumps(qr_data))
            
            return JsonResponse({
                'success': True,
                'qr_code': qr_code,
                'student_data': {
                    'name': f"{student.first_name} {student.last_name}",
                    'lrn': student.lrn,
                    'section': student.section,
                    'student_id': student.student_id
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })