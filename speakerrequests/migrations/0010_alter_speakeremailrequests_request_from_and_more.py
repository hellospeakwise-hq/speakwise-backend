import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.migrations.operations import SeparateDatabaseAndState


class Migration(migrations.Migration):

    dependencies = [
        ('speakerrequests', '0013_remove_speakerrequest_organizer_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='speakeremailrequests',
            name='request_from',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='speaker_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='speakeremailrequests',
            name='request_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='speaker_requests_received', to=settings.AUTH_USER_MODEL),
        ),
        SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='speakerrequest',
                    name='status',
                    field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('is_expired', 'Is Expired'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=20),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="CREATE INDEX IF NOT EXISTS speakerrequests_speakerrequest_status_76135cb4 ON speakerrequests_speakerrequest (status);",
                    reverse_sql="DROP INDEX IF EXISTS speakerrequests_speakerrequest_status_76135cb4;",
                ),
            ],
        ),
    ]
