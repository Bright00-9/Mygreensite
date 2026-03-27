from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import Resource, Post, Schedule
from django.contrib.auth.decorators import login_required
from .cloud_utils import render_to_pdf_report, scan_aws_full_report,fetch_cloud_data, get_boto_client,terminate_resource,get_finops_data,get_simulated_costs
from moto import mock_aws
from django.db import connection

@login_required
def dashboard_view(request):
    res = Resource.objects.all()
    total_spend = sum(r.monthly_cost for r in res) or 1
    waste_spend = sum(r.monthly_cost for r in res.filter(is_unused=True))
    green_score = round(((total_spend - waste_spend) / total_spend) * 100)
    
    context = {
        'green_score': green_score,
        'total_carbon': sum(r.carbon_waste_kg for r in res.filter(is_unused=True)),
        'resources': res.filter(is_unused=False),
        'score_offset': int(314 * (1 - (green_score / 100)))
    }
    return render(request, 'dashboard/index.html', context)
    
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
    
  
@mock_aws
def get_finops_chart_data():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    in_use_daily = []
    unused_daily = []
    
    # Get our fresh mock totals
    hourly_in_use, hourly_unused = get_simulated_costs()
    
    for day in days:
        # We multiply by 24 to get the daily cost
        # Added random.uniform to make the graph look like a real "trend"
        variation = random.uniform(0.85, 1.15)
        in_use_daily.append(round(hourly_in_use * 24 * variation, 2))
        unused_daily.append(round(hourly_unused * 24 * variation, 2))

    return {
        "labels": days,
        "in_use": in_use_daily,
        "unused": unused_daily
    }
#Replace this with your actual import if these are in cloudutils.py
# from .cloudutils import get_finops_chart_data 

@mock_aws
def finops_dashboard(request):
    # Simulating the Moto data directly here for clarity
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Simulate realistic costs ($)
    in_use_costs = [round(random.uniform(10, 15), 2) for _ in days]
    unused_costs = [round(random.uniform(2, 7), 2) for _ in days]

    context = {
        'chart_data': {
            'labels': days,
            'in_use': in_use_costs,
            'unused': unused_costs,
        }
    }
    
    return render(request, 'dashboard.html', context)

@mock_aws
def zombie_hunter(request):
    resources = fetch_cloud_data(use_mock=True)
    zombies = [r for r in resources if r['is_zombie']]
    
    if request.method == "POST" and "terminate" in request.POST:
        target_id = request.POST.get("instance_id")
        terminate_resource(target_id)
        return redirect('zombie_hunter')

    return render(request, 'dashboard/zombies.html', {'zombies': zombies})
def finops_dashboard(request):
    report_data = get_finops_data()
    context = {
        'chart_data': report_data,
    }
    
    return render(request, 'dashboard/index.html', context)


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
def post_delete(request, id):
    post = get_object_or_404(Post, id=id, author=request.user)
    post.delete()
    return redirect('dashboard:forum')
    
@login_required
def api_rightsize(request, res_id):
    r = Resource.objects.get(id=res_id)
    r.current_size = r.recommended_size
    r.save()
    return JsonResponse({"msg": "Success"})

@login_required
@mock_aws
def download_report(request):
    # 1. Get the live mock data
    resources = scan_aws_full_report()
    
    # 2. Generate the PDF buffer
    pdf_buffer = render_to_pdf_report(resources)
    
    # 3. Return the response
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Komado_Report.pdf"'
    return response


# Create your views here.
