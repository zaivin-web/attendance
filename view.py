from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import IntegrityError
import json
from .models import Student, Attendance, Subject
from .utils import send_attendance_sms, generate_qr_code, send_qr_code_email

def index(request):
    """Render the main page"""
    return render(request, 'index.html')

def qr_scanner(request):
    """Render the QR scanner page"""
    subjects = Subject.objects.all()
    return render(request, 'qrscanner.html', {'subjects': subjects})

def qr_generator(request):
    """Render the QR generator page"""
    return render(request, 'qrgenerator.html')

def registration_success(request):
    """Render the registration success page"""
    return render(request, 'registration_success.html')

@csrf_exempt
@require_http_methods(["POST"])
def scan_qr(request):
    """Process QR code scan and record attendance"""
    try:
        data = json.loads(request.body)
        lrn = data.get('lrn')
        action = data.get('action', 'time_in')  # Default to time_in

        if not lrn:
            return JsonResponse({
                'status': 'error',
                'message': 'LRN is required'
            })

        # Get the student
        try:
            student = Student.objects.get(lrn=lrn)
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            })

        # Get current time
        current_time = timezone.now()

        # Create attendance record
        attendance = Attendance.objects.create(
            student=student,
            timestamp=current_time,
            action=action
        )

        # Send SMS notification
        success, error_message = send_attendance_sms(
            student=student,
            action=action,
            timestamp=current_time,
            subject=None
        )

        if not success:
            print(f"SMS notification failed: {error_message}")

        # Get today's records
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

        # Get latest attendance records for today
        latest_time_in = Attendance.objects.filter(
            student=student,
            action='time_in',
            timestamp__range=(today_start, today_end)
        ).order_by('-timestamp').first()

        latest_time_out = Attendance.objects.filter(
            student=student,
            action='time_out',
            timestamp__range=(today_start, today_end)
        ).order_by('-timestamp').first()

        # Prepare response data
        response_data = {
            'name': student.name,
            'lrn': student.lrn,
            'section': student.section,
            'timestamp': current_time.strftime('%Y-%m-%d %I:%M %p'),
            'time_in': latest_time_in.timestamp.strftime('%I:%M %p') if latest_time_in else '-',
            'time_out': latest_time_out.timestamp.strftime('%I:%M %p') if latest_time_out else '-'
        }

        # Get today's date range
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

        # Get the latest attendance records for this student for today
        latest_time_in = Attendance.objects.filter(
            student=student,
            action='time_in',
            timestamp__range=(today_start, today_end)
        ).order_by('-timestamp').first()

        latest_time_out = Attendance.objects.filter(
            student=student,
            action='time_out',
            timestamp__range=(today_start, today_end)
        ).order_by('-timestamp').first()

        response_data['time_in'] = latest_time_in.timestamp.strftime('%I:%M %p') if latest_time_in else '-'
        response_data['time_out'] = latest_time_out.timestamp.strftime('%I:%M %p') if latest_time_out else '-'

        return JsonResponse({
            'status': 'success',
            'message': f'Attendance {action} recorded successfully',
            'data': response_data
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def register_student(request):
    """Handle student registration"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            name = f"{first_name} {last_name}"
            lrn = request.POST.get('lrn')
            section = request.POST.get('section')
            email = request.POST.get('email')
            parent_name = request.POST.get('parent_name')
            parent_phone = request.POST.get('parent_phone')

            # Format phone number
            if parent_phone:
                # Add +63 prefix and remove any non-digits
                parent_phone = '+63' + ''.join(filter(str.isdigit, parent_phone))

            # Create student
            student = Student.objects.create(
                name=name,
                lrn=lrn,
                section=section,
                email=email,
                parent_phone=parent_phone
            )

            # Generate QR code
            from .utils import generate_qr_code
            qr_data = json.dumps({
                'lrn': student.lrn,
                'student_id': student.student_id,
                'name': student.get_full_name(),
                'section': student.section
            })
            qr_code = generate_qr_code(qr_data)

            # Send email with QR code
            from .utils import send_qr_code_email
            if send_qr_code_email(student, qr_code):
                messages.success(request, 
                    f'Student registered successfully! QR code has been sent to {email}. '
                    f'Your Student ID is: {student.student_id}'
                )
            else:
                messages.warning(request,
                    f'Student registered successfully but there was an error sending the QR code email. '
                    f'Your Student ID is: {student.student_id}'
                )

            return redirect('register_success')

        except IntegrityError:
            messages.error(request, 'A student with this LRN already exists.')
        except Exception as e:
            messages.error(request, f'Error registering student: {str(e)}')

    return render(request, 'register_student.html')

@require_http_methods(["GET"])
def get_subjects(request):
    """Get list of subjects"""
    try:
        subjects = Subject.objects.all().values('id', 'code', 'name')
        return JsonResponse({
            'status': 'success',
            'subjects': list(subjects)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
