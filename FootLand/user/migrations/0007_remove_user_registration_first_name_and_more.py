# Generated by Django 5.1 on 2024-10-08 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_product_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user_registration',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='user_registration',
            name='last_name',
        ),
        migrations.AddField(
            model_name='user_registration',
            name='username',
            field=models.CharField(default='default_username', max_length=150, unique=True),
        ),
        migrations.AlterField(
            model_name='user_registration',
            name='password',
            field=models.CharField(max_length=128),
        ),
    ]