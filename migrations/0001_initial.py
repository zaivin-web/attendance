from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(blank=True, help_text='Auto-generated student ID', max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('lrn', models.CharField(max_length=12, unique=True)),
                ('section', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('parent_phone', models.CharField(blank=True, help_text="Parent's phone number for SMS notifications (e.g., +639123456789)", max_length=15, null=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(choices=[('time_in', 'Time In'), ('time_out', 'Time Out')], max_length=10)),
                ('student', models.ForeignKey(on_delete=models.deletion.CASCADE, to='attendance.student')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='attendance.subject')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]