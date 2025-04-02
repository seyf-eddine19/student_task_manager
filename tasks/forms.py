from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, GuardianProfile, Event, EventTask, Task


class ProfileForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        max_length=20,
        required=True,
        label="رقم الواتساب:",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['whatsapp_number'].initial = self.instance.profile.whatsapp_number

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self.save_m2m()
            profile, created = StudentProfile.objects.get_or_create(user=user)
            profile.whatsapp_number = self.cleaned_data.get('whatsapp_number')
            profile.save()

        return user

class AdminForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        if commit:
            user.save()
        return user

class StudentForm(UserCreationForm):
    gender = forms.ChoiceField(choices=StudentProfile.GENDER_CHOICES, required=True, label="الجنس")
    grade = forms.CharField(max_length=50, required=True, label="الصف")
    school = forms.CharField(max_length=255, required=True, label="المدرسة")
    education_department = forms.CharField(max_length=255, required=True, label="إدارة التعليم")
    profile_picture = forms.ImageField(required=False, label="صورة الطالب")

    class Meta:
        model = User
        fields = ['full_name', 'gender', 'grade', 'school', 'education_department', 'profile_picture', 'username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                grade=self.cleaned_data['grade'],
                school=self.cleaned_data['school'],
                gender=self.cleaned_data['gender'],
                education_department=self.cleaned_data['education_department'],
                profile_picture=self.cleaned_data.get('profile_picture')
            )
        return user

class GuardianForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True, label="رقم الجوال")
    relation = forms.CharField(max_length=50, required=True, label="صلة القرابة")
    students = forms.ModelMultipleChoiceField(queryset=StudentProfile.objects.all(), required=False, label="الطلاب المشرف عليهم")

    class Meta:
        model = User
        fields = ['username', 'full_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'guardian'
        if commit:
            user.save()
            guardian = GuardianProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                relation=self.cleaned_data['relation']
            )
            guardian.students.set(self.cleaned_data['students'])
        return user

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'event_date', 'students']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'students': forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox"})
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        can_delete=False
        widgets = {
            'id': forms.HiddenInput(),
            'task_name': forms.HiddenInput(),
            'status': forms.HiddenInput(),
            'start_date': forms.HiddenInput(),
            'end_date': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name != 'assigned_to':
                field.widget.attrs['readonly'] = True
            else:
                field.widget.attrs['class'] = 'form-control'

class TaskFilterForm(forms.Form):
    status = forms.MultipleChoiceField(
        choices= Task,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox"})
    )

class TaskCompletionForm(forms.ModelForm):
    class Meta:
        model = EventTask
        fields = ['completed']
