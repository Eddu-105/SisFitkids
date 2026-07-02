from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.me_view, name='me'),
    path('dashboard/summary/', views.dashboard_summary, name='dashboard-summary'),
    path('parent-portal/', views.parent_portal, name='parent-portal'),
    path('parents/', views.parents_collection, name='parents-collection'),
    path('parents/<int:parent_id>/', views.parent_detail, name='parent-detail'),
    path('students/', views.students_collection, name='students-collection'),
    path('students/<int:student_id>/', views.student_detail, name='student-detail'),
    path('class-groups/', views.class_groups_collection, name='class-groups-collection'),
    path('class-groups/<int:group_id>/', views.class_group_detail, name='class-group-detail'),
    path('payments/', views.payments_collection, name='payments-collection'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment-detail'),
    path('attendance-sessions/', views.attendance_sessions_collection, name='attendance-sessions-collection'),
    path('attendance-records/<int:record_id>/', views.attendance_record_detail, name='attendance-record-detail'),
    path('progress/', views.progress_collection, name='progress-collection'),
    path('progress/<int:progress_id>/', views.progress_detail, name='progress-detail'),
    path('announcements/', views.announcements_collection, name='announcements-collection'),
    path('announcements/<int:announcement_id>/', views.announcement_detail, name='announcement-detail'),
    path('settings/', views.settings_detail, name='settings-detail'),
    path('reports/summary/', views.reports_summary, name='reports-summary'),
    path('reports/export/', views.reports_export, name='reports-export'),
]
