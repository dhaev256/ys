from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, datetime, time

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='teacher')
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Schedule(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__role': 'teacher'})
    subject = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='schedule_photos/', blank=True, null=True, help_text='Optional photo for this session')
    
    class Meta:
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.subject} - {self.teacher.username} - {self.date} {self.start_time}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time.')
        if self.date < date.today():
            raise ValidationError('Cannot create schedule for past dates.')
    
    def get_datetime(self):
        return datetime.combine(self.date, self.start_time)

class Availability(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='availabilities')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['schedule', 'teacher']
    
    def __str__(self):
        status = "Confirmed" if self.is_confirmed else "Declined"
        return f"{self.schedule} - {self.teacher.username}: {status}"