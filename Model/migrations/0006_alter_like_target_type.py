# Generated by Django 3.2.6 on 2021-09-27 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Model', '0005_alter_like_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='target_type',
            field=models.CharField(choices=[('1', 'tie'), ('2', 'floor'), ('3', 'reply')], max_length=1),
        ),
    ]
