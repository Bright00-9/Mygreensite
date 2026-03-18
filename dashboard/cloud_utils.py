import boto3
from moto import mock_aws
from io import BytesIO
import random
from django.template.loader import get_template
from datetime import datetime, timedelta
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def get_aws_client(service, use_mock=True):
    if use_mock:
        # We manually provide dummy strings so Boto3 doesn't look for a real config file
        return boto3.client(
            service,
            region_name='us-east-1',
            aws_access_key_id='testing',
            aws_secret_access_key='testing',
            aws_session_token='testing',
        )
    # This part remains for when you eventually move to the real cloud
    return boto3.client(service)
    

def fetch_cloud_data(use_mock=True):
    ec2 = boto3.client('ec2', region_name='us-east-1')
    cw = boto3.client('cloudwatch', region_name='us-east-1')

    # SEEDING MOCK DATA (Only if Moto is active)
    if use_mock:
        # Create a Zombie
        z = ec2.run_instances(ImageId='ami-123', MinCount=1, MaxCount=1, InstanceType='t2.micro')['Instances'][0]
        # Create a Healthy Instance
        h = ec2.run_instances(ImageId='ami-456', MinCount=1, MaxCount=1, InstanceType='t2.medium')['Instances'][0]
        
        # Add "Zombie" metrics (Low CPU)
        cw.put_metric_data(
            Namespace='AWS/EC2', MetricData=[{
                'MetricName': 'CPUUtilization', 'Dimensions': [{'Name': 'InstanceId', 'Value': z['InstanceId']}],
                'Value': 1.2, 'Unit': 'Percent'
            }]
        )

    # SCANNING LOGIC
    reservations = ec2.describe_instances()['Reservations']
    resources = []
    for res in reservations:
        for inst in res['Instances']:
            i_id = inst['InstanceId']
            # Get CPU
            stats = cw.get_metric_statistics(
                Namespace='AWS/EC2', MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': i_id}],
                Period=3600, StartTime=datetime.now()-timedelta(hours=1),
                EndTime=datetime.now(), Statistics=['Average']
            )
            cpu = stats['Datapoints'][0]['Average'] if stats['Datapoints'] else 2.5
            
            # Green Score: t2.micro uses less power but t2.medium is more efficient per unit
            carbon_footprint = 0.5 if 'micro' in inst['InstanceType'] else 1.2
            
            resources.append({
                'id': i_id,
                'type': inst['InstanceType'],
                'cpu': cpu,
                'carbon': carbon_footprint,
                'is_zombie': cpu < 5.0
            })
    return resources

@mock_aws
def terminate_resource(instance_id):
    ec2 = boto3.client('ec2', region_name='us-east-1')
    ec2.terminate_instances(InstanceIds=[instance_id])
    return True


def get_boto_client(service):
    # Use us-east-1 as your standard region for Komado
    return boto3.client(service, region_name='us-east-1')

def scan_aws_full_report(use_mock=True):
    ec2 = get_boto_client('ec2')
    cw = get_boto_client('cloudwatch')
    
    # Seeding Mock Data
    if use_mock:
        ec2.run_instances(ImageId='ami-123', MinCount=1, MaxCount=1, InstanceType='t2.micro')
        ec2.run_instances(ImageId='ami-456', MinCount=1, MaxCount=1, InstanceType='t3.large')

    resources = []
    response = ec2.describe_instances()
    for res in response['Reservations']:
        for inst in res['Instances']:
            i_id = inst['InstanceId']
            # Fetch CPU
            metrics = cw.get_metric_statistics(
                Namespace='AWS/EC2', MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': i_id}],
                Period=3600, StartTime=datetime.now()-timedelta(hours=1),
                EndTime=datetime.now(), Statistics=['Average']
            )
            cpu = metrics['Datapoints'][0]['Average'] if metrics['Datapoints'] else 2.1
            resources.append({
                'id': i_id, 'type': inst['InstanceType'], 
                'cpu': cpu, 'is_zombie': cpu < 5.0,
                'carbon': 0.4 if 'micro' in inst['InstanceType'] else 1.8
            })
    return resources

def get_finops_data():
    # Define rates
    rates = {'t2.micro': 0.0116, 't3.medium': 0.0416, 'm5.large': 0.096}
    
    # Mocking a 5-day timeline
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    in_use_series = [1.20, 1.50, 1.10, 1.80, 2.10] # Mocked calculation results
    unused_series = [0.40, 0.35, 0.80, 0.45, 0.90] # Mocked waste results

    return {
        "labels": days,
        "in_use": in_use_series,
        "unused": unused_series,
        "total_waste": sum(unused_series)
    }

# Define our "FinOps" price book
INSTANCE_PRICES = {
    't2.micro': 0.0116,
    't3.medium': 0.0416,
    'm5.large': 0.096,
    'p3.2xlarge': 3.06,  # Expensive for "Zombie" simulation
}


# FinOps Price Book (Hourly Rates)
PRICES = {
    't2.micro': 0.0116,
    't3.medium': 0.0416,
    'm5.large': 0.096,
    'p3.2xlarge': 3.06
}

@mock_aws
def get_simulated_costs():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    client = boto3.client('ec2', region_name='us-east-1')

    # --- CLEANUP STEP ---
    # Terminate existing instances so data doesn't "double up" on refresh
    existing = ec2.instances.all()
    instance_ids = [i.id for i in existing]
    if instance_ids:
        client.terminate_instances(InstanceIds=instance_ids)

    # --- SEEDING STEP ---
    # 1. Create Running Resources (The "In-Use" Data)
    ec2.create_instances(ImageId='ami-12345678', MinCount=3, MaxCount=3, InstanceType='t3.medium')
    
    # 2. Create Stopped Resources (The "Zombie/Waste" Data)
    zombies = ec2.create_instances(ImageId='ami-12345678', MinCount=2, MaxCount=2, InstanceType='m5.large')
    for inst in zombies:
        inst.stop()

    # --- CALCULATION STEP ---
    in_use_hourly = 0
    unused_hourly = 0

    # Refresh the list to get current states
    for inst in ec2.instances.all():
        rate = PRICES.get(inst.instance_type, 0.0116)
        if inst.state['Name'] == 'running':
            in_use_hourly += rate
        else:
            # Simulate EBS/Idle waste (30% of rate)
            unused_hourly += (rate * 0.3)

    return in_use_hourly, unused_hourly



def render_to_pdf_report(resources):
    """
    Generates a professional GreenOps PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Komado GreenOps Cloud Report", styles['Title']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Table Data (Headers + Rows)
    data = [["Instance ID", "Type", "Carbon (kg)", "Status"]]
    for r in resources:
        status = "ZOMBIE" if r['is_zombie'] else "HEALTHY"
        data.append([r['id'], r['type'], f"{r['carbon']}", status])

    # Table Styling
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(t)
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
