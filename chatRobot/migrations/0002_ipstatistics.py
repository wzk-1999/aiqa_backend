# Generated by Django 5.1.1 on 2024-10-12 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatRobot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPStatistics',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('ip_address', models.GenericIPAddressField()),
                ('if_captcha', models.BooleanField(default=False)),
                ('request_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
