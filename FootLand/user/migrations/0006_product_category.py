# Generated by Django 5.1 on 2024-10-07 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.CharField(choices=[('kids', 'Kids'), ('mens', 'Mens'), ('womens', 'Womens')], default='mens', max_length=10),
            preserve_default=False,
        ),
    ]
