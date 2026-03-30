import boto3
from celery import shared_task
from .models import CloudConnection, ZombieResource
from .utils import calculate_carbon, calculate_carbon_impact

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



@shared_task
def hunt_for_zombies(user_id):
    conn = CloudConnection.objects.get(user_id=user_id)
    ec2 = boto3.client('ec2', aws_access_key_id=conn.access_key, 
                       aws_secret_access_key=conn.secret_key, 
                       region_name=conn.region)
    cloudwatch = boto3.client('cloudwatch', ...) 

    instances = ec2.describe_instances()

    for res in instances['Reservations']:
        for inst in res['Instances']:
            instance_id = inst['InstanceId']
            
            # Check CloudWatch: Is CPU < 1% for 1 hour?
            stats = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2', MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=..., EndTime=..., Period=3600, Statistics=['Average']
            )
            
            # If CPU is consistently low, mark as Zombie
            if stats['Datapoints'] and stats['Datapoints'][0]['Average'] < 1.0:
                carbon_impact = calculate_carbon('t3.medium', 24, conn.region)
    
                ZombieResource.objects.update_or_create(
                    resource_id=instance_id,
                    defaults={
                        'user_id': user_id,
                        'resource_type': 'EC2',
                        'waste_reason': 'CPU utilization < 1% for 1 hour',
                        'potential_savings': 15.00, # Example cost
                        'total_carbon': carbon_impact,
                    }
                )
    
                ScanSummary.objects.create(
                    user_id=user_id,
                    total_cost=current_cost,
                    total_carbon=carbon_impact # or 'impact' if defined elsewhere
                )

