from django.db import models
from django.utils import timezone
from datetime import datetime, date

class Department(models.Model):
    DEPARTMENT_CHOICES = [
        ('JHS', 'Junior High School'),
        ('SHS', 'Senior High School'),
    ]
    name = models.CharField(max_length=3, choices=DEPARTMENT_CHOICES)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)  # e.g., MATH7, ENG10
    name = models.CharField(max_length=100)  # e.g., Mathematics, English
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ['code']



class Section(models.Model):
    name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, related_name='sections')
    
    def __str__(self):
        return f"{self.name} - {self.department}"

class Student(models.Model):
    lrn = models.CharField(max_length=12, unique=True, verbose_name="LRN")
    student_id = models.CharField(max_length=20, unique=True, blank=True)  # Will be auto-generated
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(verbose_name="Date of Birth", null=True, blank=True)
    section = models.CharField(max_length=50, verbose_name="Section")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if this is a new student
        had_qr = bool(self.qr_code)  # Check if QR existed before

        # Generate student_id if not exists
        if not self.student_id:
            # Get the last ID from the database
            last_student = Student.objects.all().order_by('-student_id').first()
            if last_student:
                try:
                    # Extract the number from the last ID and increment it
                    last_id = int(last_student.student_id[3:])  # Skip the 'STD' prefix
                    new_id = last_id + 1
                except (ValueError, IndexError):
                    new_id = 1
            else:
                new_id = 1
            
            # Create new ID with leading zeros (e.g., STD0001)
            self.student_id = f'STD{new_id:04d}'
        
        # Generate QR code if not exists
        if not self.qr_code:
            import qrcode
            import json
            from django.core.files.base import ContentFile
            from io import BytesIO
            
            # Create QR code data
            qr_data = {
                'student_id': self.student_id,
                'lrn': self.lrn,
                'name': f"{self.first_name} {self.last_name}",
                'section': self.section
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
            
            # Create image from QR code
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code image
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f'qr_code_{self.student_id}.png'
            
            # Save to model's ImageField
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        # Save the model first
        super().save(*args, **kwargs)
        
        # Send email if this is a new student or QR was just generated
        if (is_new or (self.qr_code and not had_qr)) and (self.email or self.parent_email):
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                from django.utils import timezone
                from django.conf import settings
                from email.mime.image import MIMEImage
                import os
                
                # Prepare email context
                context = {
                    'student': self,
                    'school_name': 'Southville 8b National High School',
                    'current_year': timezone.now().year
                }
                
                # Create email
                subject = f'Your QR Code - School Attendance System'
                text_content = f'Your QR code for the School Attendance System is attached. Student ID: {self.student_id}'
                html_content = render_to_string('emails/qr_code_email.html', context)
                
                # Create email with both text and HTML versions
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[self.email] if self.email else [],
                    cc=[self.parent_email] if self.parent_email else []
                )
                
                # Attach HTML version
                email.attach_alternative(html_content, "text/html")
                
                # Attach QR code image if it exists and file exists
                if self.qr_code and os.path.exists(self.qr_code.path):
                    with open(self.qr_code.path, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-ID', '<qr_code>')
                        img.add_header('Content-Disposition', 'inline', filename=os.path.basename(self.qr_code.name))
                        email.attach(img)
                
                # Send email
                email.send(fail_silently=False)
                
            except Exception as e:
                # Log the error but don't prevent saving
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send QR code email to {self.get_full_name()}: {str(e)}")
    
    # Student Contact Information
    email = models.EmailField(verbose_name="Student Email", blank=True)
    address = models.TextField(verbose_name="Complete Address", blank=True)
    
    # Parent/Guardian Information
    parent_name = models.CharField(max_length=200, verbose_name="Parent/Guardian Name", blank=True)
    parent_email = models.EmailField(verbose_name="Parent/Guardian Email", blank=True)
    parent_mobile = models.CharField(max_length=11, verbose_name="Parent/Guardian Mobile Number", blank=True)
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.student_id})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ['last_name', 'first_name']

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('LATE', 'Late'),
        ('ABSENT', 'Absent'),
        ('EXCUSED', 'Excused'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        ordering = ['-date', '-time_in']
        unique_together = ['student', 'date']  # One attendance record per student per day
        
    def __str__(self):
        time_info = []
        if self.time_in:
            time_info.append(f"IN: {self.time_in.strftime('%I:%M %p')}")
        if self.time_out:
            time_info.append(f"OUT: {self.time_out.strftime('%I:%M %p')}")
        time_str = " | ".join(time_info) if time_info else "No time records"
        return f"{self.student} - {self.date} ({time_str})"
        
    def save(self, *args, **kwargs):
        # Set date from time_in if not explicitly set
        if self.time_in and not self.date:
            self.date = self.time_in.date()

        # Auto-calculate status based on time_in
        if self.time_in:
            # You can adjust these times according to your school's policy
            morning_cutoff = timezone.datetime.combine(
                self.date,
                timezone.datetime.strptime('08:00', '%H:%M').time()
            )
            if timezone.make_aware(morning_cutoff) < self.time_in:
                self.status = 'LATE'
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)  # Making this nullable temporarily
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default='PRESENT', choices=[
        ('PRESENT', 'Present'),
        ('LATE', 'Late'),
        ('ABSENT', 'Absent'),
        ('EXCUSED', 'Excused'),
    ])
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'date']
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date}"
    
    def save(self, *args, **kwargs):
        if self.time_in and not self.status == 'EXCUSED':
            # Get the first attendance for this subject today (the earliest time_in)
            first_attendance = Attendance.objects.filter(
                subject=self.subject,
                date=self.date
            ).exclude(
                id=self.id  # Exclude current attendance if it exists
            ).order_by('time_in').first()
            
            if first_attendance and first_attendance.time_in:
                # Calculate minutes difference from first attendance
                # Get time components for comparison
                time_in_time = self.time_in.time() if isinstance(self.time_in, datetime) else self.time_in
                first_time_in = first_attendance.time_in.time() if isinstance(first_attendance.time_in, datetime) else first_attendance.time_in
                
                time_diff = datetime.combine(date.today(), time_in_time) - datetime.combine(date.today(), first_time_in)
                minutes_late = int(time_diff.total_seconds() / 60)
                
                # Mark as late if more than 30 minutes after the first student's time_in
                self.status = 'LATE' if minutes_late > 30 else 'PRESENT'
            else:
                # First student is always present
                self.status = 'PRESENT'
        super().save(*args, **kwargs)
