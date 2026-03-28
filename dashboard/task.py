from celery import shared_task
import time

@shared_task
def scan_for_zombie_resources():
    print("ZOMBIE HUNTER: Starting scan of AWS resources...")
    time.sleep(5) # Simulating a cloud API call
    print("ZOMBIE HUNTER: Scan complete. 0 zombies found (for now!)")
    return "Scan Successful"
