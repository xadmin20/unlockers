# Generated by Django 4.2.4 on 2023-08-16 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partner',
            name='change_email',
        ),
        migrations.AddField(
            model_name='partner',
            name='photo',
            field=models.ImageField(blank=True, upload_to='photos/'),
        ),
    ]
