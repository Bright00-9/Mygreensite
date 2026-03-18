#!/usr/bin/env python

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard:mainboard')
        else:
            messages.error(request, 'Registration failed. Try again.')
    else:
        form = UserCreationForm()
    for field in form.fields.values():
        field.help_text = "" 
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard:mainboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('users:login')
