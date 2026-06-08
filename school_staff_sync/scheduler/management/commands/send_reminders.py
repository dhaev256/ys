from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from scheduler.models import Schedule
from django.conf import settings

class Command(BaseCommand):
    help = 'Send email reminders 24 hours before each session'

    def handle(self, *args, **options):
        now = timezone.now()
        in_24_hours = now + timedelta(hours=24)
        
        upcoming_sessions = []
        for schedule in Schedule.objects.filter(date__gte=now.date()):
            session_datetime = schedule.get_datetime()
            if session_datetime.tzinfo is None:
                session_datetime = timezone.make_aware(session_datetime)
            if now <= session_datetime <= in_24_hours:
                upcoming_sessions.append(schedule)
        
        for schedule in upcoming_sessions:
            teacher_email = schedule.teacher.email
            if not teacher_email:
                self.stdout.write(f"No email for {schedule.teacher.username}")
                continue
            
            subject = f"Reminder: {schedule.subject} class tomorrow"
            message = f"""
Dear {schedule.teacher.get_full_name() or schedule.teacher.username},

This is a reminder that you have a session tomorrow:
Subject: {schedule.subject}
Date: {schedule.date}
Time: {schedule.start_time} - {schedule.end_time}
Room: {schedule.room or 'TBA'}

Please log into the School Staff Sync system to confirm your availability.

Thank you.
            """
            send_mail(
                subject,
                message.strip(),
                getattr(settings, 'EMAIL_HOST_USER', None) or 'noreply@schoolstaffsync.com',
                [teacher_email],
                fail_silently=False,
            )
            self.stdout.write(f"Reminder sent to {teacher_email} for {schedule}")
        
        self.stdout.write(f"Processed {len(upcoming_sessions)} reminders.")