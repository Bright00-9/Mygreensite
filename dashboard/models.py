from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class Resource(models.Model):
    # Name/identifier of the cloud resource (e.g., "my-ec2-instance")
    name = models.CharField(max_length=100)
    
    # Type of cloud resource (e.g., EC2, S3, RDS, Lambda)
    resource_type = models.CharField(max_length=50)
    
    # Estimated monthly cost in USD
    monthly_cost = models.FloatField()
    
    # Current CPU utilization percentage (0.0 - 100.0)
    cpu_utilization = models.FloatField()
    
    # Whether the resource is currently unused/idle
    is_unused = models.BooleanField(default=False)
    
    # Current instance/resource size (e.g., "t2.large")
    current_size = models.CharField(max_length=50)
    
    # AI recommended optimal size to reduce waste (e.g., "t2.small")
    recommended_size = models.CharField(max_length=50)
    
    # Carbon waste in kilograms of CO2 equivalent
    carbon_waste_kg = models.FloatField()

    class Meta:
        ordering = ['-monthly_cost']  # Show most expensive resources first

    def __str__(self):  # ✅ Added missing __str__
        return f"{self.resource_type} - {self.name} (${self.monthly_cost}/mo)"
    
    def potential_savings(self):
        # Helper to check if resource can be optimized
        return self.is_unused or self.current_size != self.recommended_size

class Post(models.Model):
    # The user who created the post (optional - allows anonymous posts)
    creator = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # The main body/content of the post
    content = models.TextField()
    
    # Automatically set the timestamp when post is created
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Show newest posts first
        ordering = ['-created_at']

    def __str__(self):  # ✅ Added missing __str__
        creator_name = self.creator.username if self.creator else 'Anonymous'
        return f"Post by {creator_name} at {self.created_at}"
    
    def is_anonymous(self):
        # Helper method to check if post was made anonymously
        return self.creator is None

class CloudConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, default='AWS')
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)  # Consider encrypting this!
    region = models.CharField(max_length=50, default='us-east-1')
    created_at = models.DateTimeField(auto_now_add=True)
    is_connected = models.BooleanField(default=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):  # ✅ Fixed double underscores
        return f"{self.user.username} - {self.provider} ({self.region})"


# Individual "Zombies" found in a scan
class ZombieResource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource_id = models.CharField(max_length=100)  # e.g., i-0abc123
    resource_type = models.CharField(max_length=50)  # e.g., EC2, EBS, RDS
    waste_reason = models.CharField(max_length=255)  # e.g., "Idle for 7 days"
    potential_savings = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)
    is_terminated = models.BooleanField(default=False)

    def __str__(self):  # ✅ Added missing __str__
        return f"{self.resource_type} - {self.resource_id} ({self.user.username})"
    

class ScanSummaries(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_carbon = models.FloatField(default=0.0)  # In kgCO2e

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):  # ✅ Added missing __str__
        return f"Scan Summary for {self.user.username} at {self.timestamp}"
        

class ScanSchedule(models.Model):
    # Link to the user's connected cloud account
    user = models.OneToOneField(
        'CloudConnection', 
        on_delete=models.CASCADE, 
        related_name='shield_config'
    )
    
    SERVICE_CHOICES = [
        ('EC2', 'EC2 Zombie Hunter'),
        ('S3', 'S3 Storage Guard'),
        ('RDS', 'RDS Idle Shield'),
        ('LAMBDA', 'Lambda Monitor'),
    ]
    target_service = models.CharField(
        max_length=20, 
        choices=SERVICE_CHOICES, 
        default='EC2'
    )
    
    is_active = models.BooleanField(default=False)
    last_scan_date = models.DateTimeField(null=True, blank=True)
    total_carbon_saved = models.FloatField(default=0.0)
    
    # tore just the task name as a string instead of a ForeignKey
    periodic_task_name = models.CharField(
        max_length=200, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"Shield for {self.user} ({self.target_service})"

 
