from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.Login, name='login'),
    
    path('logout/', views.Logout, name='logout'),
    
    path('otp/', views.Otp, name='otp'),

    path('dashboard/', views.DashboardPage, name='dashboard'),
    
    path('pending_acceptance/', views.Pending_acceptance, name='pending_acceptance'),
    
    path('my_students/', views.My_students, name='my_students'),
    
    path('profile/', views.Profile, name='profile'),
    
    path('attendance/', views.Attendance, name='attendance'),
    
    path('circular/', views.Circular, name='circular'),
    
    path('assignment/', views.Assignment, name='assignment'),
    
    path('event/', views.Event, name='event'),
    
    path('examination/', views.Examination, name='examination'),
    
    path('fees/', views.Fees, name='fees'),
    
    path('media/', views.Media, name='media'),
    
    path('pdf/', views.Pdf, name='pdf'),
    
    path('photo/', views.Photo, name='photo'),
    
    path('photo/<int:circular_id>/', views.Photo, name='photo'),
    
    path('imagespecific/', views.Imagespecific, name='imagespecific'),
    
    path('store_admin_number/', views.store_admin_number, name='store_admin_number'),
    
    path('pdfdemo/', views.pdfdemo, name='pdfdemo'),
    
]