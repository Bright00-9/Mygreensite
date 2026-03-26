from django.db import models
from django.contrib.auth.models import User

class Resource(models.Model):
    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50) 
    monthly_cost = models.FloatField()
    cpu_utilization = models.FloatField()
    is_unused = models.BooleanField(default=False) 
    current_size = models.CharField(max_length=50)
    recommended_size = models.CharField(max_length=50)
    carbon_waste_kg = models.FloatField()

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Schedule(models.Model):
    env_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    start_time = models.CharField(max_length=5, default="06:00")
    end_time = models.CharField(max_length=5, default="20:00")
