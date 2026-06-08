from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/photo/', views.update_profile_photo, name='update_profile_photo'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_update, name='schedule_update'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    path('teacher/schedule/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher/availability/<int:schedule_pk>/', views.update_availability, name='update_availability'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/success/', views.teacher_creation_success, name='teacher_creation_success'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('change-password/', views.change_password, name='change_password'),
]