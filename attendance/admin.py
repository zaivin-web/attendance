from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Student, Attendance

# Customize admin site
admin.site.site_header = 'School Attendance System'
admin.site.site_title = 'School Attendance System'
admin.site.index_title = 'Attendance Management'

def resend_qr_code(modeladmin, request, queryset):
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings
    import os
    from django.utils import timezone
    from email.mime.image import MIMEImage
    
    for student in queryset:
        if student.qr_code:
            # Prepare email context
            context = {
                'student': student,
                'school_name': 'Southville 8b National High School',
                'current_year': timezone.now().year
            }
            
            # Create email with both text and HTML versions
            subject = f'Your QR Code - School Attendance System'
            text_content = f'Your QR code for the School Attendance System is attached. Student ID: {student.student_id}'
            html_content = render_to_string('emails/qr_code_email.html', context)
            
            # Create the email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[student.email] if student.email else [],
                cc=[student.parent_email] if hasattr(student, 'parent_email') and student.parent_email else []
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Attach QR code
            qr_path = student.qr_code.path
            if os.path.exists(qr_path):
                with open(qr_path, 'rb') as f:
                    # Create MIMEImage
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<qr_code>')
                    img.add_header('Content-Disposition', 'inline', filename='qr_code.png')
                    email.attach(img)
                    
                try:
                    email.send(fail_silently=False)
                    modeladmin.message_user(request, f"QR code resent successfully to {student.get_full_name()}")
                except Exception as e:
                    modeladmin.message_user(request, f"Error sending QR code to {student.get_full_name()}: {str(e)}", level='ERROR')
        else:
            modeladmin.message_user(request, f"No QR code found for {student.get_full_name()}", level='WARNING')

resend_qr_code.short_description = "Resend QR code via email"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'lrn', 'section', 'email', 'get_parent_mobile', 'get_qr_code')
    list_filter = ('section',)
    search_fields = ('student_id', 'first_name', 'last_name', 'lrn', 'section', 'email', 'parent_mobile')
    readonly_fields = ('student_id', 'qr_code', 'qr_code_display')  # Make student_id and qr_code read-only
    actions = [resend_qr_code]  # Add the resend action

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Name'
    
    def get_parent_mobile(self, obj):
        return obj.parent_mobile or '-'
    get_parent_mobile.short_description = "Parent's Mobile"

    def get_qr_code(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" />', obj.qr_code.url)
        return '-'
    get_qr_code.short_description = 'QR Code'

    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="200" height="200" />', obj.qr_code.url)
        return 'No QR Code available'
    qr_code_display.short_description = 'QR Code Preview'

    fieldsets = (
        ('Student Information', {
            'fields': (
                'student_id',  # Show as read-only
                ('first_name', 'last_name'),
                'lrn',
                'section',
                'email'
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'parent_name',
                'parent_email',
                'parent_mobile'
            )
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_code_display'),
        })
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time_display', 'status')
    list_filter = ('date', 'status')
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id')
    date_hierarchy = 'date'
    ordering = ('-date', '-time_in')
    
    def time_display(self, obj):
        time_in = obj.time_in.strftime('%I:%M %p') if obj.time_in else '-'
        time_out = obj.time_out.strftime('%I:%M %p') if obj.time_out else '-'
        return format_html('IN: {} <br> OUT: {}', time_in, time_out)
    time_display.short_description = 'Time'

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'student',
                'date',
                ('time_in', 'time_out'),
                'status'
            )
        }),
    )