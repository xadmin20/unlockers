# Generated by Django 4.2.4 on 2023-08-26 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0002_alter_request_car'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='unique_path_field',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]