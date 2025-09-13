import qrcode
from io import BytesIO
import base64
import subprocess
import json
import os
import platform
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def generate_qr_code(data):
    """Generate QR code from data and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to BytesIO buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    
    # Convert to base64 string
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return qr_base64

def send_qr_code_email(student, qr_code_base64):
    """Send QR code to student's email"""
    try:
        if not hasattr(settings, 'EMAIL_HOST'):
            raise ValueError("Email settings not configured. Please check your settings.py")

        subject = 'Your Attendance QR Code'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        to_email = student.email

        if not to_email:
            raise ValueError("Student email address is missing")

        # Prepare context for email template
        context = {
            'student': student,
            'qr_code': qr_code_base64  # Add QR code to template context
        }

        try:
            # Render HTML content
            html_content = render_to_string('emails/qr_code_email.html', context)
            text_content = strip_tags(html_content)
        except Exception as template_error:
            print(f"Template error: {template_error}")
            raise ValueError("Error rendering email template")

        # Create email message
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to_email]
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        try:
            # Attach QR code image
            qr_image_data = base64.b64decode(qr_code_base64)
            email.attach('qr_code.png', qr_image_data, 'image/png')
        except Exception as qr_error:
            print(f"QR code attachment error: {qr_error}")
            raise ValueError("Error attaching QR code to email")

        # Send email
        try:
            email.send(fail_silently=False)
            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as send_error:
            print(f"Email sending error: {send_error}")
            # Check common configuration issues
            if not settings.EMAIL_HOST:
                raise ValueError("EMAIL_HOST not configured")
            if not settings.EMAIL_PORT:
                raise ValueError("EMAIL_PORT not configured")
            if getattr(settings, 'EMAIL_USE_TLS', False) and not settings.EMAIL_HOST_PASSWORD:
                raise ValueError("EMAIL_HOST_PASSWORD required for TLS")
            raise ValueError(f"Failed to send email: {str(send_error)}")

    except Exception as e:
        print(f"Error in send_qr_code_email: {str(e)}")
        return False

def check_termux_api():
    """
    Check if Termux-API is installed and accessible
    Returns:
        bool: True if Termux-API is available, False otherwise
    """
    try:
        # Check if we're running on Android/Termux
        import platform
        if not platform.system() == 'Linux' or 'ANDROID_ROOT' not in os.environ:
            print("Not running on Android - SMS will be logged instead of sent")
            return False
            
        result = subprocess.run(['termux-sms-list'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("Termux-API not found - SMS will be logged instead of sent")
        return False

def validate_phone_number(phone):
    """
    Validate and format phone number
    Returns:
        tuple: (bool, str) - (is_valid, formatted_number)
    """
    # Remove any non-digit characters
    clean_number = ''.join(filter(str.isdigit, phone))
    
    # Check if number is valid (at least 10 digits)
    if len(clean_number) < 10:
        return False, None
        
    return True, clean_number

def send_attendance_sms(student, action, timestamp, subject=None, retry_count=2):
    """
    Send SMS notification about student attendance using Termux-API
    
    Parameters:
        student: Student object containing student information
        action: String indicating 'time_in' or 'time_out'
        timestamp: DateTime object of when the attendance was recorded
        subject: Optional subject name for the attendance record
        retry_count: Number of times to retry sending SMS if it fails
    
    Returns:
        tuple: (bool, str) - (success, error_message)
    """
    # First check if Termux-API is available
    if not check_termux_api():
        return False, "Termux-API is not installed or accessible"
        
    try:
        # Format timestamp
        time_str = timestamp.strftime('%I:%M %p')  # e.g., "09:30 AM"
        date_str = timestamp.strftime('%B %d, %Y')  # e.g., "September 13, 2025"
        
        # Validate action
        if action not in ['time_in', 'time_out']:
            return False, f"Invalid action: {action}"
            
        # Format the message in Filipino
        if action == 'time_in':
            action_text = 'pumasok sa paaralan'
        else:
            action_text = 'umuwi na galing paaralan'
            
        message = f"ATTENDANCE UPDATE:\n\nAng inyong anak na si {student.name} ay {action_text} ngayong {date_str} sa oras na {time_str}"
        
        if subject:
            message += f"\n\nSubject: {subject}"
            
        message += "\n\nIto ay automated message. Huwag po reply."
            
        # Get parent/guardian phone number
        try:
            phone_number = student.parent_phone  # Make sure your student model has this field
        except AttributeError:
            return False, "Student model does not have parent_phone field"
            
        if not phone_number:
            return False, f"No phone number found for student {student.name}"
            
        # Validate phone number
        is_valid, formatted_number = validate_phone_number(phone_number)
        if not is_valid:
            return False, f"Invalid phone number format: {phone_number}"
            
        # Try sending SMS with retries
        for attempt in range(retry_count):
            try:
                    # Check if running on Android/Termux
                if platform.system() == 'Linux' and 'ANDROID_ROOT' in os.environ:
                    # Use termux-sms-send to send the message
                    result = subprocess.run(
                        ['termux-sms-send', '-n', formatted_number, message],
                        capture_output=True,
                        text=True,
                        timeout=30  # 30 second timeout
                    )
                    
                    if result.returncode == 0:
                        print(f"SMS sent successfully to {formatted_number}")
                        return True, "SMS sent successfully"
                    else:
                        error = result.stderr or "Unknown error"
                        print(f"Attempt {attempt + 1}: Error sending SMS: {error}")
                        
                        # If we have more attempts, wait before retrying
                        if attempt < retry_count - 1:
                            import time
                            time.sleep(2)  # Wait 2 seconds before retrying
                            continue
                        
                        return False, f"Failed to send SMS after {retry_count} attempts: {error}"
                else:
                    # Development mode - just log the SMS
                    print("\n=== DEVELOPMENT MODE: SMS Log ===")
                    print(f"Would send SMS to: {formatted_number}")
                    print(f"Message: {message}")
                    print("================================\n")
                    return True, "SMS logged (Development mode)"
                    
            except subprocess.TimeoutExpired:
                error = f"SMS command timed out on attempt {attempt + 1}"
                print(error)
                if attempt == retry_count - 1:
                    return False, error
                    
            except Exception as e:
                error = f"Unexpected error on attempt {attempt + 1}: {str(e)}"
                print(error)
                if attempt == retry_count - 1:
                    return False, error
                    
    except Exception as e:
        error = f"Error preparing SMS: {str(e)}"
        print(error)
        return False, error