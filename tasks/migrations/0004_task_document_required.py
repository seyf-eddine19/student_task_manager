# Generated by Django 5.0.7 on 2025-04-02 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_alter_task_phase_alter_task_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='document_required',
            field=models.BooleanField(default=False),
        ),
    ]
