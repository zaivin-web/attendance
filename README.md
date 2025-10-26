# Attendance Management System

This project is a Django-based attendance management system designed to streamline student registration, attendance tracking, and notification processes.

This project is a Django-based attendance management system designed to streamline student registration, attendance tracking, and notification processes.

## Features

- Student registration with QR code generation
- Attendance scanning via QR codes
- Admin dashboard for managing students and attendance
- Email notifications for attendance events
- Export attendance data

## Project Structure

- `attendance/` - Main Django app with models, views, utilities, and management commands
- `attendance_project/` - Django project settings and configuration
- `media/` - Stores generated QR codes
- `static/` - Static files (CSS, JS, audio)
- `templates/` - HTML templates for views and emails
- `db.sqlite3` - SQLite database
- `manage.py` - Django management script
- `requirements.txt` - Python dependencies

## Setup Instructions

1. **Clone the repository**

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Apply migrations:**

   ```bash
   python manage.py migrate
   ```

4. **Run the development server:**

   ```bash
   python manage.py runserver
   ```

5. **Access the app:**

   Open your browser and go to `http://localhost:8000`

## Management Commands

Custom commands are available in `attendance/management/commands/`:

- `cleanup_sections.py` - Cleans up section data
- `reset_sections.py` - Resets section data

## License

Specify your license here.

## Author

- [zaivin-web](https://github.com/zaivin-web)
