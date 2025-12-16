from django.db import migrations
from django.conf import settings

def create_default_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.get_or_create(
        id=settings.SITE_ID,
        defaults={'domain': '127.0.0.1:8000', 'name': 'Clinic Local'}
    )

def reverse_func(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=settings.SITE_ID).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('clinic', '0001_initial'),  # ← replace with your last migration
    ]

    operations = [
        migrations.RunPython(create_default_site, reverse_func),
    ]