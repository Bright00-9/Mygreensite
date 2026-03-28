import boto3
from celery import shared_task
from .models import CloudConnection

@shared_task
def scan_user_aws(user_id):
    conn = CloudConnection.objects.get(user_id=user_id)
    
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=conn.access_key,
        aws_secret_access_key=conn.secret_key,
        region_name=conn.region
    )

    instances = ec2.describe_instances()
    
    # Simple FinOps/GreenOps Logic
    total_instances = 0
    running_instances = 0
    estimated_hourly_cost = 0.0
    carbon_footprint_estimate = 0.0 # kgCO2e

    for reservation in instances['Reservations']:
        for inst in reservation['Instances']:
            total_instances += 1
            if inst['State']['Name'] == 'running':
                running_instances += 1
                # Rough FinOps Estimate ($0.05/hr for a t3.medium-ish)
                estimated_hourly_cost += 0.05 
                # Rough GreenOps Estimate (0.02 kgCO2e per hour)
                carbon_footprint_estimate += 0.02

    # In a real app, you'd save these results to a ScanResult model
    print(f"RESULTS: {running_instances} running out of {total_instances}")
    return {
        'cost': estimated_hourly_cost,
        'carbon': carbon_footprint_estimate,
        'zombies': total_instances - running_instances
    }
