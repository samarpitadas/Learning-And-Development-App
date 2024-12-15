from django.contrib import admin
from django.urls import path, include
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('create-course/', views.create_course, name='create_course'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('assign-course/<int:course_id>/', views.assign_course, name='assign_course'),
    path('mark-module-complete/<int:module_id>/', views.mark_module_complete, name='mark_module_complete'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('submit-feedback/<int:course_id>/', views.submit_feedback, name='submit_feedback'),
    path('create_request/', views.create_request, name='create_request'),
    path('update_request_status/<pk>/', views.update_request_status, name='update_request_status'),
    path('view_request/<pk>/', views.view_request, name='view_request'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('generate-credentials/', views.generate_employee_credentials, name='generate_employee_credentials'),
]
