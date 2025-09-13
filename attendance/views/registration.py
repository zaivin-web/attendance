from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.conf import settings
from ..models import Student
import qrcode
import json
from io import BytesIO

def register_student(request):
    if request.method == 'POST':
        try:
            # Get student data from form
            # Create student object with separated first_name and last_name
            # Create and save student first to generate student_id
            student = Student.objects.create(
                first_name=request.POST.get('first_name', '').strip(),
                last_name=request.POST.get('last_name', '').strip(),
                lrn=request.POST.get('lrn'),
                email=request.POST.get('email'),
                section=request.POST.get('section'),
                parent_mobile=request.POST.get('parent_mobile', ''),  # Parent's mobile number
                parent_name=request.POST.get('parent_name', ''),  # Parent's name
                parent_email=request.POST.get('parent_email', '')  # Parent's email
            )
            
            # Generate QR code data
            qr_data = {
                'id': student.id,
                'student_id': student.student_id,
                'name': student.get_full_name(),
                'lrn': student.lrn,
                'section': student.section
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Generate safe filename using student_id (which should now be available)
            if not student.student_id:
                raise ValueError("Student ID was not generated correctly")
            
            # Save QR code to BytesIO for both file and email
            qr_buffer = BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Save QR code to student model
            filename = f'qr_code_{student.student_id}.png'
            student.qr_code.save(filename, ContentFile(qr_buffer.getvalue()), save=True)
            
            # Create a fresh buffer for email attachment
            qr_buffer = BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)

            try:
                # Prepare email
                subject = 'Your Attendance QR Code'
                html_message = render_to_string('emails/qr_code_email.html', {
                    'student': student,
                    'school_name': settings.SCHOOL_NAME
                })

                # Create email message
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[student.email]
                )
                email.content_subtype = "html"

                # Attach QR code to email
                email.attach(filename, qr_buffer.getvalue(), 'image/png')

                # Send email
                email.send(fail_silently=False)
                print(f"Email sent successfully to {student.email}")
                messages.success(request, 'Registration successful! QR code has been sent to your email.')
                return redirect('register_student')
            except Exception as e:
                print(f"Email error: {str(e)}")  # For debugging
                messages.warning(request, 'Registration successful but failed to send email. Please contact administrator.')
                return redirect('register_student')
                
        except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                return redirect('register_student')
    
    return render(request, 'register_student.html')