# Generated by Django 3.1.12 on 2025-04-03 10:04

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entity_type', models.CharField(choices=[('PRODUCT', 'Product'), ('ORDER', 'Order'), ('SHIPMENT', 'Shipment'), ('BLOG', 'Blog Post')], max_length=20)),
                ('entity_id', models.UUIDField()),
                ('customer_id', models.UUIDField(blank=True, null=True)),
                ('customer_name', models.CharField(max_length=100)),
                ('customer_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('content', models.TextField()),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Review'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('FLAGGED', 'Flagged for Review')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('parent_comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='comments.comment')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CommentFlag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('customer_id', models.UUIDField(blank=True, null=True)),
                ('reason', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flags', to='comments.comment')),
            ],
            options={
                'unique_together': {('comment', 'customer_id')},
            },
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['entity_type', 'entity_id'], name='comments_co_entity__3f865a_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['customer_id'], name='comments_co_custome_d8ab5a_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['status'], name='comments_co_status_2720ea_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['created_at'], name='comments_co_created_5f6a12_idx'),
        ),
    ]
