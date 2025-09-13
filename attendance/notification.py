from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import subprocess
import platform
import os
import re

def validate_phone_number(number):
    """Validate and format phone number"""
    # Remove any non-digit characters
    cleaned = re.sub(r'\D', '', number)
    
    # Check if it's a valid Philippine mobile number
    if len(cleaned) == 11 and cleaned.startswith('09'):
        return True, cleaned
    elif len(cleaned) == 10 and cleaned.startswith('9'):
        return True, '0' + cleaned
    return False, None

def check_termux_api():
    """Check if termux-api is installed and accessible"""
    try:
        result = subprocess.run(['which', 'termux-sms-send'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def send_attendance_notification(student, action, subject=None, timestamp=None):
    """Send both email and SMS notifications about student attendance"""
    success_email = False
    success_sms = False
    messages = []

    # Send Email if parent email is available
    if student.parent_email:
        context = {
            'student_name': student.get_full_name(),
            'action': 'arrived at school' if action == 'time_in' else 'left school',
            'time': timestamp.strftime('%I:%M %p'),
            'date': timestamp.strftime('%B %d, %Y'),
            'subject': subject.name if subject else None,
        }
        
        # Render email template
        html_message = render_to_string('emails/attendance_notification.html', context)
        plain_message = strip_tags(html_message)
        
        action_type = "Time In" if action == 'time_in' else "Time Out"
        
        try:
            send_mail(
                subject=f'Student {action_type} Notification - {student.get_full_name()}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.parent_email],
                html_message=html_message,
                fail_silently=True,
            )
            success_email = True
            messages.append("Email sent successfully")
        except Exception as e:
            messages.append(f"Email failed: {str(e)}")
    
    # Send SMS if parent mobile is available
    if hasattr(student, 'parent_mobile') and student.parent_mobile:
        # Format the message in Filipino
        time_str = timestamp.strftime('%I:%M %p')
        date_str = timestamp.strftime('%B %d, %Y')
        
        if action == 'time_in':
            action_text = 'pumasok sa paaralan'
        else:
            action_text = 'umuwi na galing paaralan'
            
        message = f"ATTENDANCE UPDATE:\n\nAng inyong anak na si {student.get_full_name()} ay {action_text} ngayong {date_str} sa oras na {time_str}"
        
        if subject:
            message += f"\n\nSubject: {subject}"
            
        message += "\n\nIto ay automated message. Huwag po reply."
        
        # Validate phone number
        is_valid, formatted_number = validate_phone_number(student.parent_mobile)
        
        if is_valid:
            # Check if we're running on Android/Termux
            if platform.system() == 'Linux' and 'ANDROID_ROOT' in os.environ:
                try:
                    # Use termux-sms-send
                    result = subprocess.run(
                        ['termux-sms-send', '-n', formatted_number, message],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        success_sms = True
                        messages.append("SMS sent successfully")
                    else:
                        messages.append(f"SMS failed: {result.stderr}")
                except Exception as e:
                    messages.append(f"SMS failed: {str(e)}")
            else:
                # Development mode - just log the SMS
                print("\n=== DEVELOPMENT MODE: SMS Log ===")
                print(f"Would send SMS to: {formatted_number}")
                print(f"Message: {message}")
                print("================================\n")
                success_sms = True
                messages.append("SMS logged (Development mode)")
        else:
            messages.append(f"Invalid phone number format: {student.parent_mobile}")
    
    return {
        'success': success_email or success_sms,
        'email_sent': success_email,
        'sms_sent': success_sms,
        'messages': messages
    }