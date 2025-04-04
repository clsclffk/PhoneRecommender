# Generated by Django 4.2.19 on 2025-03-15 23:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hobbies', '0002_alter_hobbytrends_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisResults',
            fields=[
                ('analysis_id', models.AutoField(primary_key=True, serialize=False)),
                ('selected_keywords', models.JSONField()),
                ('freq_ratio_samsung', models.JSONField()),
                ('freq_ratio_apple', models.JSONField()),
                ('related_words_samsung', models.JSONField()),
                ('related_words_apple', models.JSONField()),
                ('sentiment_samsung_score', models.JSONField()),
                ('sentiment_apple_score', models.JSONField()),
                ('sentiment_samsung_ratio', models.JSONField()),
                ('sentiment_apple_ratio', models.JSONField()),
                ('sentiment_top_sentences', models.JSONField(default=dict)),
                ('keyword_monthly_trend', models.JSONField(default=dict)),
                ('analysis_summary', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hobby_id', models.ForeignKey(db_column='hobby_id', on_delete=django.db.models.deletion.CASCADE, to='hobbies.hobbykeywords')),
            ],
            options={
                'verbose_name': 'Analysis result',
                'verbose_name_plural': 'Analysis results',
                'db_table': 'analysis_results',
                'managed': True,
                'unique_together': {('hobby_id', 'selected_keywords')},
            },
        ),
    ]
