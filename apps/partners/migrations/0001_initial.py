# Generated by Django 4.2.4 on 2023-08-12 19:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('booking', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Withdraw',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Withdraw amount')),
                ('attachment_file', models.FileField(upload_to='invoices/%Y/%m/%d/', verbose_name='Attachment file')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date create')),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'Not Paid'), (2, 'Paid'), (3, 'Declined')], default=1, verbose_name='Status')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comment')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partner_withdraw', to=settings.AUTH_USER_MODEL, verbose_name='Partner')),
            ],
            options={
                'verbose_name': 'Withdraw',
                'verbose_name_plural': 'Withdraws',
            },
        ),
        migrations.CreateModel(
            name='Transactions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Transaction amount')),
                ('balance', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Balance after transactions')),
                ('type_transactions', models.PositiveSmallIntegerField(choices=[(1, 'INCOME'), (2, 'WITHDRAW'), (3, 'REFUND'), (4, 'CANCELLATION')], verbose_name='Type transactions')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date create')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_income', to='booking.order', verbose_name='Order')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partner_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Partner')),
                ('withdraw', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='withdraw_invoice', to='partners.withdraw', verbose_name='Withdraw')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
            },
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(blank=True, max_length=100, verbose_name='Company name')),
                ('phone', models.CharField(blank=True, max_length=255, verbose_name='Phone')),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Balance')),
                ('change_email', models.EmailField(blank=True, max_length=254, verbose_name='Change email')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Partner')),
            ],
            options={
                'verbose_name': 'Partner',
                'verbose_name_plural': 'Partners',
            },
        ),
    ]
