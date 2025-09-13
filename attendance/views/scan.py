from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from datetime import datetime, timedelta

from ..models import Student, Attendance
from ..notification import send_attendance_notification

def scan_qr(request):
    """QR code scanner view"""
    if request.method == 'GET':
        return render(request, 'qrscanner.html')
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            lrn = data.get('lrn')
            action = data.get('action')
            
            if not lrn:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid QR Code - LRN is required'
                })

            try:
                student = Student.objects.get(lrn=lrn)
            except Student.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': f'No student found with LRN: {lrn}'
                })
                
            # Get or create today's attendance record
            today = timezone.now().date()
            timestamp = timezone.now()
            
            if action == 'time_in':
                # For time in, check for existing attendance
                attendance = Attendance.objects.filter(
                    student=student,
                    date=today
                ).first()
                
                if not attendance:
                    attendance = Attendance.objects.create(
                        student=student,
                        date=today,
                        time_in=timestamp
                    )
                    send_attendance_notification(student, 'time_in', None, timestamp)
                    message = f"Time in recorded for {student.get_full_name()}"
                else:
                    message = f"{student.get_full_name()} has already timed in at {attendance.time_in.strftime('%I:%M %p')}"
            else:  # time_out
                # First check for any open attendance records (with time_in but no time_out)
                open_attendance = Attendance.objects.filter(
                    student=student,
                    date=today,
                    time_in__isnull=False,
                    time_out__isnull=True
                ).order_by('-time_in')

                if not open_attendance.exists():
                    # Get the last attendance record for today
                    last_attendance = Attendance.objects.filter(
                        student=student,
                        date=today
                    ).order_by('-time_in').first()
                    
                    if not last_attendance:
                        message = f"Error: {student.get_full_name()} has not timed in yet today"
                    elif last_attendance.time_out:
                        message = f"Error: {student.get_full_name()} has already timed out at {last_attendance.time_out.strftime('%I:%M %p')}"
                    else:
                        # Create a new attendance record if the last one is complete
                        attendance = Attendance.objects.create(
                            student=student,
                            date=today,
                            time_in=timestamp
                        )
                        message = f"Time in recorded for {student.get_full_name()}"
                        return JsonResponse({
                            'status': 'success',
                            'message': message,
                            'data': {
                                'name': student.get_full_name(),
                                'lrn': student.lrn,
                                'section': student.section,
                                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'time_in': attendance.time_in.strftime('%I:%M %p'),
                                'time_out': None
                            }
                        })
                    
                    return JsonResponse({
                        'status': 'error',
                        'message': message
                    })

                # Get the latest open attendance
                attendance = open_attendance.first()
                attendance.time_out = timestamp
                attendance.save()
                
                try:
                    # Use Django's timezone utilities to ensure proper timezone handling
                    time_in = timezone.localtime(attendance.time_in)
                    time_out = timezone.localtime(attendance.time_out)
                    
                    # Calculate duration
                    duration = time_out - time_in
                    hours = int(duration.total_seconds() / 3600)
                    minutes = int((duration.total_seconds() % 3600) / 60)
                    
                    duration_str = f"{hours}h {minutes}m"
                except Exception as e:
                    print(f"Error calculating duration: {str(e)}")
                    duration_str = "calculation error"
                
                # Send notification
                send_attendance_notification(student, 'time_out', None, timestamp)
                
                message = f"Time out recorded for {student.get_full_name()}. Duration: {duration_str}"
            
            return JsonResponse({
                'status': 'success',
                'message': message,
                'data': {
                    'name': student.get_full_name(),
                    'lrn': student.lrn,
                    'section': student.section,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'time_in': attendance.time_in.strftime('%I:%M %p') if attendance and attendance.time_in else None,
                    'time_out': attendance.time_out.strftime('%I:%M %p') if attendance and attendance.time_out else None
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid QR Code format'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            lrn = data.get('lrn')
            action = data.get('action')
            
            if not lrn:
                return JsonResponse({
                    'status': 'error',
                    'message': 'LRN is required'
                })
            
            try:
                student = Student.objects.get(lrn=lrn)
            except Student.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': f'No student found with LRN: {lrn}'
                })
                
            timestamp = timezone.now()
            
            # Get or create today's attendance record
            today = timezone.now().date()
            if action == 'time_in':
                # For time in, create new record
                attendance = Attendance.objects.filter(
                    student=student,
                    date=today
                ).first()
                
                if not attendance:
                    attendance = Attendance.objects.create(
                        student=student,
                        date=today,
                        time_in=None,
                        time_out=None
                    )
            else:
                # For time out, get the last attendance record for today
                attendance = Attendance.objects.filter(
                    student=student,
                    date=today,
                    time_in__isnull=False,
                    time_out__isnull=True
                ).last()

            if action == 'time_in':
                if attendance.time_in is None:
                    attendance.time_in = timestamp
                    attendance.save()
                    # Send email notification
                    send_attendance_notification(student, 'time_in', None, timestamp)
                    message = f"Time in recorded for {student.get_full_name()}"
                else:
                    message = f"{student.get_full_name()} has already timed in at {attendance.time_in.strftime('%I:%M %p')}"
            else:  # time_out
                if not attendance or attendance.time_in is None:
                    message = f"Error: {student.get_full_name()} has not timed in yet"
                elif attendance.time_out is not None:
                    message = f"{student.get_full_name()} has already timed out at {attendance.time_out.strftime('%I:%M %p')}"
                else:
                    # Only time that hasn't been timed out yet
                    attendance.time_out = timestamp
                    attendance.save()
                    # Send email notification
                    send_attendance_notification(student, 'time_out', None, timestamp)
                    
                    # Calculate duration
                    duration = attendance.time_out.replace(tzinfo=None) - attendance.time_in.replace(tzinfo=None)
                    hours = int(duration.total_seconds() / 3600)
                    minutes = int((duration.total_seconds() % 3600) / 60)
                    
                    message = f"Time out recorded for {student.get_full_name()}. Duration: {hours}h {minutes}m"
            
            return JsonResponse({
                'status': 'success',
                'message': message,
                'data': {
                    'name': student.get_full_name(),
                    'lrn': student.lrn,
                    'section': student.section,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'time_in': attendance.time_in.strftime('%I:%M %p') if attendance.time_in else None,
                    'time_out': attendance.time_out.strftime('%I:%M %p') if attendance.time_out else None
                }
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

# Exempt from CSRF for QR code scanning
scan_qr = csrf_exempt(scan_qr)