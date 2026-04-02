from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

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
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Schedule(models.Model):
    env_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    start_time = models.CharField(max_length=5, default="06:00")
    end_time = models.CharField(max_length=5, default="20:00")


class CloudConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, default='AWS')
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255) # In a real app, we would encrypt this!
    region = models.CharField(max_length=50, default='us-east-1')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.provider} ({self.region})"


# Individual "Zombies" found in a scan
class ZombieResource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource_id = models.CharField(max_length=100) # e.g., i-0abc123
    resource_type = models.CharField(max_length=50) # e.g., EC2, EBS, RDS
    waste_reason = models.CharField(max_length=255) # e.g., "Idle for 7 days"
    potential_savings = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)
    is_terminated = models.BooleanField(default=False)
    

class ScanSummary(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_carbon = models.FloatField(default=0.0) # In kgCO2e
    
    class Meta:
        ordering = ['-timestamp']

 
