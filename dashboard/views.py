from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Resource, Post, Schedule, CloudConnection, ScanSummary, ZombieResource
from django.contrib.auth.decorators import login_required
import boto3
import json
from .cloud_utils import render_to_pdf_report, scan_aws_full_report,fetch_cloud_data, get_boto_client,terminate_resource,get_finops_data,get_simulated_costs
from moto import mock_aws
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from .tasks import scan_user_aws
from django.template.loader import get_template
from xhtml2pdf import pisa

  

def dashboard_home(request):
    # Get the last 7 days of data
    last_week = timezone.now() - timedelta(days=7)
    history = ScanSummary.objects.filter(
        user=request.user, 
        timestamp__gte=last_week
    ).order_by('timestamp')

    # Formatting data for Chart.js
    labels = [s.timestamp.strftime("%a") for s in history] # "Mon", "Tue", etc.
    costs = [s.total_cost for s in history]
    carbon = [s.total_carbon for s in history]

    # Latest Score for the Gauge
    latest = history.last()
    # Simplified Eco-Score (0-100). Lower carbon = higher score.
    eco_score = max(0, 100 - (latest.total_carbon * 10)) if latest else 0

    context = {

    }
    
    has_connection = CloudConnection.objects.filter(user=request.user).exists()
    
    # Only try to fetch scans if a connection exists
    latest_scan = None
    if has_connection:
        latest_scan = ScanSummary.objects.filter(user=request.user).order_by('-timestamp').first()

    context = {
        'has_connection': has_connection,
        'scan': latest_scan,
        'labels': labels,
        'costs': costs,
        'carbon': carbon,
        'eco_score': eco_score,
        'latest': latest
    }
    
    return render(request, 'dashboard/index.html', context)

# dashboard/views.py

def calculate_eco_score(total_carbon):
    # Let's say 10kg CO2e is our "Max" limit for a good score
    max_threshold = 10.0
    score = 100 - (total_carbon / max_threshold * 100)
    return max(0, min(100, score)) # Keep between 0 and 100


@login_required
@mock_aws
def index(request):
    # This acts as the main "Connect & Scan" dashboard
    resources = []
    if request.method == "POST" and "scan" in request.POST:
        resources = fetch_cloud_data(use_mock=True)
    posts = Post.objects.all().order_by('-created_at')
    # Mock FinOps Data for Chart.js
    context = {
        'resources': resources,
        'labels': ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        'cost_data': [120, 150, 110, 90, 200, 130, 170]
    }
    
    # Finance against time (Mocked for the last 7 days)
    finance_labels = ["Mar 05", "Mar 06", "Mar 07", "Mar 08", "Mar 09", "Mar 10", "Mar 11"]
    finance_values = [450, 420, 510, 380, 390, 410, 350] # Cost in Cedis

    return render(request, 'dashboard/index.html', context, {
        'resources': resources,
        'posts': posts,
        'fin_labels': finance_labels,
        'fin_data': finance_values
    })
    


def finops_dashboard(request):
    last_7_days = timezone.now() - timedelta(days=7)
    data_points = ScanSummary.objects.filter(
        user=request.user, 
        timestamp__gte=last_7_days
    ).order_by('timestamp')

    # Convert to JSON for the script
    context = {
        'labels': json.dumps([dp.timestamp.strftime('%m/%d') for dp in data_points]),
        'cost_data': json.dumps([float(dp.total_cost) for dp in data_points]),
        'carbon_data': json.dumps([dp.total_carbon for dp in data_points]),
    }
    return render(request, 'dashboard/finops.html', context)






def finops_dashboard(request):
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Get data for the chart
    chart_data = ScanSummary.objects.filter(
        user=request.user, 
        timestamp__gte=seven_days_ago
    ).order_by('timestamp')

    # Prepare data for Chart.js
    labels = [data.timestamp.strftime("%b %d") for data in chart_data]
    costs = [data.total_cost for data in chart_data]

    context = {
        'labels': labels,
        'costs': costs,
        'latest_scan': chart_data.last(),
    }
    return render(request, 'dashboard/finops.html', context)

def zombie_graveyard(request):
    zombies = ZombieResource.objects.filter(user=request.user, is_terminated=False)
    return render(request, 'dashboard/.html', {'zombies': zombies})


def terminate_resource(request, zombie_id):
    zombie = get_object_or_404(ZombieResource, id=zombie_id, user=request.user)
    
    zombie.is_terminated = True
    zombie.save()
    
    messages.success(request, f"Resource {zombie.resource_id} has been exorcised!")
    return redirect('zombie_graveyard')


@login_required
def shield_view(request):
    sched = Schedule.objects.first()
    return render(request, 'dashboard/shield.html', {'sched': sched})
    

@login_required
@mock_aws
def shield_scheduler(request):
    status = ""
    if request.method == "POST":
        instance_id = request.POST.get("instance_id")
        start_time = request.POST.get("start_time") # e.g., "0600"
        end_time = request.POST.get("end_time")   
        ec2 = get_boto_client('ec2')
        ec2.create_tags(
            Resources=[instance_id],
            Tags=[
                {'Key': 'AutoSchedule', 'Value': 'true'},
                {'Key': 'ScheduleRange', 'Value': f"{start_time}-{end_time}"}
            ]
        )
        status = f"Schedule set for {instance_id}: {start_time} to {end_time}"

    resources = fetch_cloud_data()
    return render(request, 'dashboard/shield.html', {'resources': resources, 'status': status})
    

@login_required
def forum_view(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        print(f"DEBUG: Attempting to save post. Content: {content[:20]}")
        if content and request.user.is_authenticated:
            new_post = Post.objects.create(creator=request.user, content=content)
            print(f"DEBUG: Post created with ID {new_post.id} by {request.user.username}")
            return redirect('dashboard:forum')
        else:
            print("DEBUG: Post failed. Content empty or User not logged in.")
    Post.objects.filter(creator__isnull=True).update(creator=request.user)

    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'dashboard/posts.html', {'posts': posts})

    
@login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        if post.creator == request.user:
            post.delete()
            print(f"DEBUG: Post {post_id} deleted successfully.")
        else:
            print(f"DEBUG: Permission denied for user {request.user}")
            
    return redirect('dashboard:forum')


@login_required
def api_rightsize(request, res_id):
    r = Resource.objects.get(id=res_id)
    r.current_size = r.recommended_size
    r.save()
    return JsonResponse({"msg": "Success"})

@login_required
def generate_pdf_report(request):
    # Fetch data
    try:
        latest_scan = ScanSummary.objects.filter(user=request.user).latest('timestamp')
        zombies = ZombieResource.objects.filter(user=request.user)
    except ScanSummary.DoesNotExist:
        return HttpResponse("No scan data found. Run a manual scan first.")

    # Context for the template
    context = {
        'scan': latest_scan,
        'zombies': zombies,
    }

    # Create the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Komado_Report.pdf"'
    
    template = get_template('dashboard/pdf_report.html')
    html = template.render(context)

    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



def connect_aws(request):
    if request.method == "POST":
        access_key = request.POST.get('access_key')
        secret_key = request.POST.get('secret_key')
        region = request.POST.get('region')
        
        # Save or update the connection
        conn, created = CloudConnection.objects.update_or_create(
            user=request.user,
            defaults={'access_key': access_key, 'secret_key': secret_key, 'region': region}
        )
        messages.success(request, "AWS Account Connected Successfully!")
        return redirect('dashboard:forum')
    
    return render(request, 'dashboard/connect_aws.html')

def run_manual_scan(request):
    if request.method == "POST":
        # Pass the user ID so the task knows which AWS keys to pull from your database
        scan_user_aws.delay(request.user.id)
        
        # Give the user feedback
        from django.contrib import messages
        messages.success(request, "Initiating full account scan...")
        
        return redirect('dashboard:forum')
    return redirect('dashboard:forum')

