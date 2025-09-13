from django.core.management.base import BaseCommand
from attendance.models import Section, Department, Subject

class Command(BaseCommand):
    help = 'Reset sections to default configuration'

    def handle(self, *args, **kwargs):
        # First, remove any existing sections
        Section.objects.all().delete()

        # Create departments
        jhs, _ = Department.objects.get_or_create(name='JHS')
        shs, _ = Department.objects.get_or_create(name='SHS')

        # Create sections with their subjects
        jhs_subjects_7 = Subject.objects.filter(code__in=['MATH7', 'ENG7', 'SCI7', 'FIL7'])
        jhs_subjects_8 = Subject.objects.filter(code__in=['MATH8', 'ENG8', 'SCI8', 'FIL8'])
        shs_subjects = Subject.objects.filter(code__in=['CALC1', 'PHYS1', 'CHEM1', 'BIO1', 'COMP1'])

        # Create Grade 7-A
        grade_7a = Section.objects.create(name='Grade 7-A', department=jhs)
        grade_7a.subjects.set(jhs_subjects_7)
        self.stdout.write(f'Created section: Grade 7-A with {grade_7a.subjects.count()} subjects')

        # Create Grade 8-A
        grade_8a = Section.objects.create(name='Grade 8-A', department=jhs)
        grade_8a.subjects.set(jhs_subjects_8)
        self.stdout.write(f'Created section: Grade 8-A with {grade_8a.subjects.count()} subjects')

        # Create Grade 11-STEM
        grade_11 = Section.objects.create(name='Grade 11-STEM', department=shs)
        grade_11.subjects.set(shs_subjects)
        self.stdout.write(f'Created section: Grade 11-STEM with {grade_11.subjects.count()} subjects')