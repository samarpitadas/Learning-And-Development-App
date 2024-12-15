from django.db import migrations

def remove_duplicate_feedbacks(apps, schema_editor):
    CourseFeedback = apps.get_model('accounts', 'CourseFeedback')
    seen = set()
    for feedback in CourseFeedback.objects.all():
        key = (feedback.course_id, feedback.employee_id)
        if key in seen:
            feedback.delete()
        else:
            seen.add(key)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_alter_coursefeedback_unique_together'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_feedbacks),
        migrations.AlterUniqueTogether(
            name='coursefeedback',
            unique_together={('course', 'employee')},
        ),
    ]
