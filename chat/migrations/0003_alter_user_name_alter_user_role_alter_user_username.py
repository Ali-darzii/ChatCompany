# Generated by Django 4.2 on 2023-12-22 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_groups_groupmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=90, null=True, unique=True),
        ),
    ]
