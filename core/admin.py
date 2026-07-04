from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Announcement,
    AppSetting,
    AttendanceRecord,
    AttendanceSession,
    ClassGroup,
    ParentProfile,
    Payment,
    ProgressEvaluation,
    Student,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol del sistema', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dni', 'phone', 'emergency_phone', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'dni', 'phone')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'parent', 'class_group', 'birth_date', 'status')
    list_filter = ('status', 'class_group')
    search_fields = ('first_name', 'last_name', 'parent__user__first_name', 'parent__user__last_name')


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'day_of_week', 'start_time', 'end_time', 'capacity', 'age_range', 'color', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('name', 'age_range')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'concept', 'amount', 'due_date', 'paid_date', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('student__first_name', 'student__last_name', 'concept')


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('class_group', 'date', 'created_at')
    list_filter = ('class_group', 'date')
    inlines = [AttendanceRecordInline]


@admin.register(ProgressEvaluation)
class ProgressEvaluationAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'weight_kg', 'height_cm', 'strength', 'endurance', 'coordination', 'flexibility')
    list_filter = ('date',)
    search_fields = ('student__first_name', 'student__last_name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'parent', 'is_active', 'created_at')
    list_filter = ('audience', 'is_active', 'created_at')
    search_fields = ('title', 'body', 'parent__user__first_name', 'parent__user__last_name')


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ('academy_name', 'teacher_name', 'phone', 'default_monthly_fee')
