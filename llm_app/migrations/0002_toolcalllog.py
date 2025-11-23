from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('conversation_app', '0002_message_external_message_id_and_more'),
        ('llm_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToolCallLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('tool_name', models.CharField(max_length=128)),
                ('arguments', models.JSONField(blank=True, default=dict)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('success', models.BooleanField(default=True)),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tool_calls', to='conversation_app.message')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='toolcalllog',
            index=models.Index(fields=['tool_name', 'created_at'], name='llm_app_too_tool_nam_39140b_idx'),
        ),
    ]
