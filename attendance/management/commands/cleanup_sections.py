from django.core.management.base import BaseCommand
from attendance.models import Section

class Command(BaseCommand):
    help = 'Clean up unused sections in the database'

    def handle(self, *args, **kwargs):
        # Get sections without any subjects
        empty_sections = Section.objects.filter(subjects__isnull=True)
        
        if empty_sections.exists():
            self.stdout.write("Found sections without subjects:")
            for section in empty_sections:
                self.stdout.write(f"- {section.name} ({section.department})")
                section.delete()
            self.stdout.write(self.style.SUCCESS("Successfully removed empty sections"))
        else:
            self.stdout.write("No empty sections found")