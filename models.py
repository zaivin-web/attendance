from django.db import models

class Student(models.Model):
    student_id = models.CharField(max_length=10, unique=True, blank=True, help_text="Auto-generated student ID")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    lrn = models.CharField(max_length=12, unique=True)
    section = models.CharField(max_length=50)
    email = models.EmailField()
    parent_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Parent's phone number for SMS notifications (e.g., +639123456789)"
    )

    def save(self, *args, **kwargs):
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
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.lrn}"
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['name']

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "Time In" if self.time_in else "Not Started"
        if self.time_out:
            status = "Completed"
        return f"{self.student.name} - {self.date} - {status}"

    class Meta:
        ordering = ['-timestamp']
