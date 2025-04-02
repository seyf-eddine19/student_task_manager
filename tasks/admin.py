from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, GuardianProfile, Event, Task, EventTask

class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'full_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'full_name')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'grade', 'school', 'gender', 'education_department')
    list_filter = ('grade', 'gender', 'education_department')
    search_fields = ('user__full_name', 'school')

class GuardianProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'relation')
    search_fields = ('user__full_name', 'phone_number')

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_date', 'created_by', 'student_count')
    list_filter = ('event_date',)
    search_fields = ('name', 'description')
    filter_horizontal = ('students',)

class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'phase')
    search_fields = ('name',)
    list_filter = ('phase',)

class EventTaskAdmin(admin.ModelAdmin):
    list_display = ('event', 'student', 'task', 'completed')
    list_filter = ('completed', 'event')
    search_fields = ('student__user__full_name', 'task__name')

# تسجيل النماذج مع لوحة التحكم
admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(GuardianProfile, GuardianProfileAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(EventTask, EventTaskAdmin)
