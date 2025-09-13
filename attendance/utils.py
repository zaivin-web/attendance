import qrcode
from io import BytesIO
import base64
from django.core.mail import send_mail, EmailMultiAlternatives
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

def send_attendance_notification(student, action, subject=None, timestamp=None):
    """Send email notification to parent/guardian"""
    if not student.parent_email:
        return False
        
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
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_qr_code_email(student, qr_code_base64):
    """Send QR code to student's email"""
    subject = 'Your Attendance QR Code'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = student.email

    # Prepare context for email template
    context = {
        'student': student,
    }

    # Render HTML content
    html_content = render_to_string('emails/qr_code_email.html', context)
    text_content = strip_tags(html_content)

    # Create email message
    email = EmailMultiAlternatives(
        subject,
        text_content,
        from_email,
        [to_email]
    )

    # Attach HTML version
    email.attach_alternative(html_content, "text/html")
    
    # Attach QR code image
    qr_image_data = base64.b64decode(qr_code_base64)
    email.attach('qr_code.png', qr_image_data, 'image/png')
    
    # Send email
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False