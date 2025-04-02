from django.urls import reverse_lazy, reverse
from django.forms import HiddenInput, inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Max

from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView, RedirectView, ListView, FormView, UpdateView, DetailView, DeleteView

from .models import Event, Task, StudentProfile, EventTask, User
from .forms import (
    ProfileForm, AdminForm, StudentForm, GuardianForm , EventForm, TaskForm, TaskFilterForm
)

def custom_403(request, exception):
    return render(request, '403.html', {}, status=403)

def custom_404(request, exception):
    return render(request, '404.html', {}, status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

class IndexView(LoginRequiredMixin, TemplateView):
    """عرض الصفحة الرئيسية"""
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_event = Event.objects.last() 
        students = StudentProfile.objects.filter(events=last_event) if last_event else []
        # حساب المهام لكل طالب وتمريرها إلى السياق
        
        for student in students:
            student.prep_count = student.tasks_prep_count(last_event)
            student.action_count = student.tasks_action_count(last_event)
            student.setup_count = student.tasks_setup_count(last_event)
            student.execution_count = student.tasks_execution_count(last_event)
            student.total_count = student.tasks_total_count(last_event)
            student.progress = student.task_progress(last_event)
      
        students = sorted(students, key=lambda student: student.progress, reverse=True)

        context["event"] = last_event
        context["events"] = Event.objects.all()
        context["students"] = students
        return context

class StudentProgressAPI(LoginRequiredMixin, View):
    """إرجاع بيانات تقدم الطلاب بتنسيق JSON لـ AJAX"""
    
    def get(self, request):
        last_event = Event.objects.last()
        if not last_event:
            return JsonResponse({"error": "لا يوجد حدث"}, status=404)

        students_data = []
        students = StudentProfile.objects.filter(events=last_event)

        for student in students:
            students_data.append({
                "id": student.id,
                "full_name": student.user.full_name,
                "profile_picture": student.profile_picture.url if student.profile_picture else "/static/default.png",
                "progress": student.task_progress(last_event),
                "prep_count": student.tasks_prep_count(last_event),
                "action_count": student.tasks_action_count(last_event),
                "setup_count": student.tasks_setup_count(last_event),
                "execution_count": student.tasks_execution_count(last_event),
            })

        return JsonResponse({"students": students_data})

class LogoutView(LoginRequiredMixin, RedirectView):
    """تسجيل الخروج وإعادة التوجيه لصفحة تسجيل الدخول"""
    pattern_name = 'login'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)

class ProfileView(LoginRequiredMixin, FormView):
    """عرض وتحديث الملف الشخصي للمستخدم"""
    template_name = 'users/profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_form"] = PasswordChangeForm(self.request.user)
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'تم تحديث الملف الشخصي بنجاح!')
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """التعامل مع تحديث الملف الشخصي وكلمة المرور"""
        form = self.get_form()
        password_form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'تم تحديث كلمة المرور بنجاح!')
            return self.form_valid(form)

        return self.form_invalid(form)

# Form Views Mixin
class FormViewMixin(FormView):
    def get_object(self):
        """Retrieve object if updating, or return None for creation."""
        pk = self.kwargs.get("pk")
        print(f"🟢 Form is valid. is_update: {pk}")  # Debugging
        if pk:
            return get_object_or_404(self.model, pk=pk)
        return None

    def get_form_kwargs(self):
        """Pass instance to form if updating"""
        kwargs = super().get_form_kwargs()
        obj = self.get_object()
        if obj:
            kwargs["instance"] = obj
        return kwargs

    def get_initial(self):
        """Prefill form with existing data if updating."""
        obj = self.get_object()
        if obj:
            return {field.name: getattr(obj, field.name) for field in obj._meta.fields}
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def get_success_url(self):
        """إعادة التوجيه إلى الصفحة السابقة إذا كانت موجودة"""
        return self.request.GET.get("next", self.success_url)

    def form_valid(self, form):
        """Validate form and handle saving"""
        obj = form.save(commit=False) 
        is_update = self.get_object() is not None 
        print(f"🟢 Form is valid. is_update: {is_update}")  # Debugging
        obj.save()
        self.object = obj 
        form.save_m2m()
 
        if is_update:
            messages.success(self.request, "تم تحديث البيانات بنجاح!")
        else:
            messages.success(self.request, "تم إضافة البيانات بنجاح!")

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        messages.error(self.request, "حدث خطأ أثناء حفظ البيانات. يرجى التحقق من المدخلات.")
        return super().form_invalid(form)

# User Views
class UserListView(ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    permission_required = 'auth.view_user'

class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'users/user_delete.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'auth.delete_user'

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'تم حذف البيانات بنجاح.')
        return response

class UserFormView(LoginRequiredMixin, FormViewMixin):
    model = User
    form_class = AdminForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

    def get_form(self, form_class=None):
        """إرجاع النموذج مع تعيين الكائن في وضع التحديث."""
        form = super().get_form(form_class)
        obj = self.get_object()
        if obj:  # تحديث مستخدم موجود
            form.instance = obj
            form.fields['password1'].widget = HiddenInput()
            form.fields['password1'].required = False
            form.fields['password2'].widget = HiddenInput()
            form.fields['password2'].required = False
            form.fields['username'].widget.attrs['readonly'] = True
        return form
    
    # def form_valid(self, form):
    #     """Validate form and handle saving"""
    #     obj = form.save(commit=False)
    #     is_update = self.get_object() is not None

    #     if not is_update:
    #         # إنشاء مستخدم جديد، يجب ضبط كلمة المرور
    #         obj.set_password(form.cleaned_data['password'])

    #     obj.save()
    #     form.save_m2m()  # حفظ العلاقات ManyToMany
    #     # تحديث أو إنشاء StudentProfile
    #     profile, created = StudentProfile.objects.get_or_create(user=obj)
    #     profile.whatsapp_number = form.cleaned_data.get('whatsapp_number')
    #     profile.save()


    #     messages.success(self.request, "تم تحديث بيانات المستخدم بنجاح!" if is_update else "تم إنشاء المستخدم بنجاح!")

    #     return redirect(self.get_success_url())  # إعادة التوجيه إلى القائمة

# Event Views
class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'

class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = 'events/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        students = event.students.all()
        for student in students:
            student.total_count = student.tasks_total_count(event)
            student.progress = student.task_progress(event)
        
        context["students"] = students
        context["event"] = event
        return context

class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/delete.html'
    success_url = reverse_lazy('event_list')

    def dispatch(self, request, *args, **kwargs):
        """ Restrict access to only admins. """
        if not request.user.is_admin():
            raise PermissionDenied  # This triggers your custom 403 handler
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'تم حذف البيانات بنجاح.')
        return response

class EventFormView(LoginRequiredMixin, FormViewMixin):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    success_url = reverse_lazy('event_list')

    def dispatch(self, request, *args, **kwargs):
        """ Restrict access to only admins. """
        if not request.user.is_admin():
            raise PermissionDenied  # This triggers your custom 403 handler
        return super().dispatch(request, *args, **kwargs)
    
    # def get_success_url(self):
    #     """Redirect to update page if editing, otherwise event list."""
    #     if self.object:  # Ensure object exists
    #         return reverse_lazy('event_update', kwargs={'pk': self.object.pk})
    #     return reverse_lazy('event_list')  # Default to event list

class EventStudentTaskDetailView(ListView):
    model = EventTask
    template_name = "events/student_tasks.html"  # تأكد من إنشاء هذا القالب
    context_object_name = "tasks"

    def dispatch(self, request, *args, **kwargs):
        """ Restrict access to only admins. """
        student = get_object_or_404(StudentProfile, pk=self.kwargs["student_id"])

        if not (request.user.is_admin or request.user == student.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        event = get_object_or_404(Event, pk=self.kwargs["pk"])
        student = get_object_or_404(StudentProfile, pk=self.kwargs["student_id"])
        return EventTask.objects.filter(event=event, student=student)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(StudentProfile, pk=self.kwargs["student_id"])
        student.total_count = student.tasks_total_count(self.kwargs["pk"])
        student.progress = student.task_progress(self.kwargs["pk"])
        context["event"] = get_object_or_404(Event, pk=self.kwargs["pk"])
        context["student"] = student 
        return context


# Users
class AdminFormView(LoginRequiredMixin, FormViewMixin):
    model = User
    form_class = AdminForm
    template_name = 'users/admin_form.html'
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):
        """ Restrict access to only admins. """
        if not request.user.is_admin():
            raise PermissionDenied  # This triggers your custom 403 handler
        return super().dispatch(request, *args, **kwargs)
    

class StudentFormView(LoginRequiredMixin, FormViewMixin):
    model = User
    form_class = StudentForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):
        """ Restrict access to only admins. """
        if not request.user.is_admin():
            raise PermissionDenied  # This triggers your custom 403 handler
        return super().dispatch(request, *args, **kwargs)
    

class GuardianFormView(LoginRequiredMixin, FormViewMixin):
    model = User
    form_class = GuardianForm
    template_name = 'users/parent_form.html'
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):
        """ Restrict access to only admins. """
        if not request.user.is_admin():
            raise PermissionDenied  # This triggers your custom 403 handler
        return super().dispatch(request, *args, **kwargs)
    

# Tasks Views
class TaskListView(LoginRequiredMixin, ListView):
    model = EventTask
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        latest_event = Event.objects.filter(event_tasks__student__user=self.request.user).aggregate(Max("event_date"))["event_date__max"]
        return EventTask.objects.filter(student__user=self.request.user, event__event_date=latest_event)


class CompleteTaskView(LoginRequiredMixin, UpdateView):
    model = EventTask
    fields = ['completed', 'document'] 

    def get_object(self, queryset=None):
        task = super().get_object(queryset)
        if task.student.user != self.request.user:
            raise PermissionDenied
        return task

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        document = request.FILES.get('document')
        task.completed = True
        if document:
            task.document = document
        task.save()
        return redirect('task_list') 