from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from attendance.models import Student, Attendance

def qrscanner(request):
    """View function to render the QR scanner page"""
    return render(request, 'qrscanner.html')

@csrf_exempt
@require_http_methods(["POST"])
def scan_qr(request):
    try:
        print("Received data:", request.body.decode('utf-8'))  # Debug log
        data = json.loads(request.body)
        print("Parsed JSON:", data)  # Debug log
        lrn = data.get("lrn")
        action = data.get("action", "time_in")
        
        student = Student.objects.get(lrn=lrn)
        
        # Record attendance
        now = timezone.now()
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=now.date()
        )
        
        if action == "time_in":
            if attendance.time_in:
                time_str = attendance.time_in.strftime("%I:%M %p")
                return JsonResponse({
                    "status": "error",
                    "message": f"Time in already recorded for {student.first_name} today at {time_str}"
                }, status=400)
                
            attendance.time_in = now
            # Set status based on time
            if now.time().hour >= 8:
                attendance.status = "LATE"
            else:
                attendance.status = "PRESENT"
                
        elif action == "time_out":
            if not attendance.time_in:
                return JsonResponse({
                    "status": "error",
                    "message": "Cannot time out without time in record"
                }, status=400)
                
            if attendance.time_out:
                time_str = attendance.time_out.strftime("%I:%M %p")
                return JsonResponse({
                    "status": "error",
                    "message": f"Time out already recorded for {student.first_name} today at {time_str}"
                }, status=400)
                
            attendance.time_out = now
        
        attendance.save()
        
        # Format times for response
        time_in_str = attendance.time_in.strftime("%I:%M %p") if attendance.time_in else None
        time_out_str = attendance.time_out.strftime("%I:%M %p") if attendance.time_out else None
        current_time_str = now.strftime("%I:%M %p")
        
        # Prepare response data
        response_data = {
            "status": "success",
            "message": f"Successfully recorded {action} for {student.first_name} at {current_time_str}",
            "student": {
                "name": student.get_full_name(),
                "lrn": student.lrn,
                "section": student.section
            },
            "attendance": {
                "status": attendance.status,
                "time_in": time_in_str,
                "time_out": time_out_str
            }
        }
        
        return JsonResponse(response_data)
        
    except Student.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Student not found"
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }, status=500)
