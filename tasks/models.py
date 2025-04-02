from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_migrate, m2m_changed
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'مسؤول'),
        ('student', 'طالب'),
        ('guardian', 'ولي أمر'),
    ]
    full_name = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="نوع الحساب")

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["full_name", "role"] 

    def is_admin(self):
        return self.role == "admin"

    def is_student(self):
        return self.role == "student"

    def is_guardian(self):
        return self.role == "guardian"

class StudentProfile(models.Model):
    GENDER_CHOICES = [
        ('ذكر', 'ذكر'),
        ('أنثى', 'أنثى'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    grade = models.CharField(max_length=50, verbose_name="الصف")
    school = models.CharField(max_length=255, verbose_name="المدرسة")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="الجنس")
    education_department = models.CharField(max_length=255, verbose_name="إدارة التعليم")
    profile_picture = models.ImageField(upload_to="students/", blank=True, null=True, verbose_name="صورة الطالب")

    def tasks_prep_count(self, event):
        return self._get_task_count(event, "مرحلة الاستعداد")

    def tasks_action_count(self, event):
        return self._get_task_count(event, "مرحلة الإجراءات")

    def tasks_setup_count(self, event):
        return self._get_task_count(event, "مرحلة التهيئة")

    def tasks_execution_count(self, event):
        return self._get_task_count(event, "مرحلة التنفيذ")

    def tasks_total_count(self, event):
        total_tasks = self.tasks.filter(event=event).count()
        completed_tasks = self.tasks.filter(event=event, completed=True).count()
        return f"{completed_tasks}/{total_tasks}"

    def task_progress(self, event):
        total_tasks = self.tasks.filter(event=event).count()
        completed_tasks = self.tasks.filter(event=event, completed=True).count()
        return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    def _get_task_count(self, event, phase):
        total_tasks = self.tasks.filter(event=event, task__phase=phase).count()
        completed_tasks = self.tasks.filter(event=event, task__phase=phase, completed=True).count()
        return f"{completed_tasks}/{total_tasks}"

    def __str__(self):
        return f"{self.user.full_name}"

class GuardianProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guardian_profile")
    phone_number = models.CharField(max_length=15, verbose_name="رقم الجوال")
    relation = models.CharField(max_length=50, verbose_name="صلة القرابة")  # أب، أم، أخ، أخت
    students = models.ManyToManyField(StudentProfile, related_name="guardians", verbose_name="الطلاب المشرف عليهم")
    
    def __str__(self):
        return f"ولي الأمر: أ.{self.user.full_name} ({self.phone_number})"

class Event(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الحدث")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الحدث")
    event_date = models.DateField(verbose_name="تاريخ الحدث")
    students = models.ManyToManyField(StudentProfile, related_name="events", verbose_name="الطلاب المشاركون", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='منشئ المشروع')

    def student_count(self):
        return self.students.count()

    def create_event_tasks(self, new_students):
        """إنشاء مهام الحدث فقط للطلاب الجدد."""
        tasks = Task.objects.all().distinct()
        event_tasks = [
            EventTask(event=self, student=student, task=task)
            for student in new_students
            for task in tasks
        ]
        EventTask.objects.bulk_create(event_tasks, ignore_conflicts=True)

    def __str__(self):
        return self.name

@receiver(m2m_changed, sender=Event.students.through)
def update_event_tasks(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    يتم استدعاء هذا الإجراء عند إضافة أو إزالة طلاب من الحدث.
    """
    if action == "post_add":
        # الطلاب الجدد الذين تم إضافتهم إلى الحدث
        new_students = StudentProfile.objects.filter(id__in=pk_set)
        if new_students.exists():
            instance.create_event_tasks(new_students=new_students)
            print("✅ تمت إضافة مهام للطلاب الجدد.")

    elif action == "post_remove":
        # حذف المهام المرتبطة بالطلاب الذين تمت إزالتهم
        EventTask.objects.filter(event=instance, student_id__in=pk_set).delete()
        print("❌ تم حذف المهام الخاصة بالطلاب الذين تمت إزالتهم.")

class Task(models.Model):
    phase = models.CharField(max_length=255, unique=False, verbose_name="اسم المرحلة")
    name = models.CharField(max_length=255, unique=True, verbose_name="اسم المهمة")
    document_required = models.BooleanField(default=False) 
    
    class Meta:
        unique_together = ("phase", "name")
       

    def __str__(self):
        return f"{self.phase} - {self.name}"

class EventTask(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_tasks", verbose_name="الحدث")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="tasks", verbose_name="الطالب")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="event_tasks", verbose_name="المهمة")
    completed = models.BooleanField(default=False, verbose_name="تم الإنجاز")
    document = models.FileField(upload_to="event_tasks/", blank=True, null=True, verbose_name="المستند (إن وجد)")

    class Meta:
        unique_together = ("event", "student", "task") 
        
    def __str__(self):
        return f"{self.student.user.full_name} - {self.task.name} - {self.event.name}"


# إضافة البيانات تلقائيًا بعد الترحيل (`migrate`)
@receiver(post_migrate)
def create_default_data(sender, **kwargs):
    if sender.name == "tasks":  # تأكد من أن الإشارة تعمل فقط لهذا التطبيق
        default_data = {
            "مرحلة الاستعداد": [
                ["الانتهاء من عمل المشروع (الاختراع)", True],
                ["استكمال براءة الاختراع للمشروع", True],
            ],
            "مرحلة الإجراءات": [
                ["إصدار التأشيرة", True],
                ["إصدار موافقة ولي الأمر في أبشر", True],
                ["رفع المستندات الرسمية (صورة الجواز والتأشيرة والهوية والصورة الشخصية)", True],
            ],
            "مرحلة التهيئة": [
                ["رفع الملصق العلمي (البوستر) عربي وانجليزي وفرنسي", True],
                ["طباعة الملصق العلمي (البوستر) وفق المقاسات المطلوبة", True],
                ["حضور لقاء التأهيل عن بعد ١", False],
                ["حضور لقاء التأهيل عن بعد ٢", False],
                ["حضور لقاء التأهيل عن بعد ٣", False],
                ["حضور اللقاء العام عن بعد", False],
            ],
            "مرحلة التنفيذ": [
                ["الوصول للمطار مبكرا", False],
                ["التواجد في مقر العرض ١", False],
                ["التواجد في مقر العرض ٢", False],
                ["التواجد في مقر العرض ٣", False],
                ["التواجد في مقر العرض ٤", False],
                ["التواجد في مقر العرض ٥", False],
            ],
        }
        try:
            for phase_name, tasks in default_data.items():
                for task_name, document in tasks:
                    task, created = Task.objects.get_or_create(phase=phase_name, name=task_name, document_required=document)
                    if created:
                        logger.info(f"✔ تم إضافة المهمة: {phase_name} - {task_name}")

            logger.info("✅ تم إنشاء البيانات الافتراضية بنجاح!")

        except Exception as e:
            logger.error(f"❌ خطأ أثناء إنشاء البيانات الافتراضية: {e}")
