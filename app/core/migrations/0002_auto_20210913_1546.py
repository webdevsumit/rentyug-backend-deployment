# Generated by Django 3.1.13 on 2021-09-13 10:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='Rating',
            field=models.FloatField(default=4),
        ),
        migrations.CreateModel(
            name='RequestedService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Title', models.CharField(max_length=100)),
                ('Description', models.TextField()),
                ('ContactInfo', models.CharField(max_length=100)),
                ('Date', models.DateField(auto_now=True)),
                ('completed', models.BooleanField(default=False)),
                ('User', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]