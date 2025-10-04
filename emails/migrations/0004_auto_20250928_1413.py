from django.db import migrations
import uuid

def generate_template_ids(apps, schema_editor):
    EmailTemplate = apps.get_model("emails", "EmailTemplate")
    for template in EmailTemplate.objects.all():
        if not template.template_id:
            template.template_id = uuid.uuid4().hex[:8].upper()
            template.save(update_fields=["template_id"])

class Migration(migrations.Migration):

    dependencies = [
        ("emails", "0003_emailtemplate_template_id"),
    ]

    operations = [
        migrations.RunPython(generate_template_ids, migrations.RunPython.noop),
    ]
