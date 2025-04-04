# Generated by Django 4.2.19 on 2025-03-15 23:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HobbyKeywords',
            fields=[
                ('hobby_id', models.AutoField(primary_key=True, serialize=False)),
                ('hobby_name', models.CharField(max_length=50, unique=True)),
                ('keyword_list', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Hobby Keyword',
                'verbose_name_plural': 'Hobby Keywords',
                'db_table': 'hobby_keywords',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='HobbyTrends',
            fields=[
                ('trends_id', models.AutoField(primary_key=True, serialize=False)),
                ('gender', models.CharField(choices=[('M', '남성'), ('F', '여성')], max_length=1)),
                ('age_group', models.CharField(choices=[('10s', '10대'), ('20s', '20대'), ('30s', '30대'), ('40s', '40대'), ('50s', '50대'), ('60s', '60대')], max_length=10)),
                ('selected_keywords', models.JSONField(default=list)),
                ('count', models.IntegerField(default=0)),
                ('date', models.DateField(auto_now_add=True)),
                ('hobby_id', models.ForeignKey(db_column='hobby_id', on_delete=django.db.models.deletion.CASCADE, to='hobbies.hobbykeywords')),
            ],
            options={
                'verbose_name': 'Hobby Trend',
                'verbose_name_plural': 'Hobby Trends',
                'db_table': 'hobby_trends',
                'managed': True,
                'unique_together': {('hobby_id', 'gender', 'age_group', 'date')},
            },
        ),
    ]
