from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path("api/student-progress/", views.StudentProgressAPI.as_view(), name="student-progress-api"),

    # تسجيل الدخول والخروج
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # المستخدمون
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/student/', views.StudentFormView.as_view(), name='student_create'),
    path('users/create/parent/', views.GuardianFormView.as_view(), name='parent_create'),
    path('users/create/', views.UserFormView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', views.UserFormView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # الأحداث
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/<int:pk>', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/student/<int:student_id>/', views.EventStudentTaskDetailView.as_view(), name='student_event_tasks_detail'),
    path('events/create/', views.EventFormView.as_view(), name='event_create'),
    path('events/<int:pk>/update/', views.EventFormView.as_view(), name='event_update'),
    path('events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),

    # المهام
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/complete/', views.CompleteTaskView.as_view(), name='complete_task'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# معالجة الأخطاء
handler403 = 'tasks.views.custom_403'
handler404 = 'tasks.views.custom_404'
handler500 = 'tasks.views.custom_500'
