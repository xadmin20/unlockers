# Generated by Django 4.2.4 on 2023-08-30 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0002_alter_smstemplate_message2_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('subject', models.CharField(max_length=200)),
                ('html_content', models.TextField()),
            ],
        ),
    ]
