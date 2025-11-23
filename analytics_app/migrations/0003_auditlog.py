from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics_app', '0002_dailykpi'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('event_type', models.CharField(max_length=128)),
                ('actor', models.CharField(blank=True, max_length=128)),
                ('target', models.CharField(blank=True, max_length=128)),
                ('payload', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['event_type', 'created_at'], name='analytics__event_ty_4a8260_idx'),
        ),
    ]
