from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'accounts/profile.html')


@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    return render(request, 'accounts/change_password.html')


@login_required
def user_list(request):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    query = request.GET.get('q', '')
    users = User.objects.all()
    if query:
        users = users.filter(Q(username__icontains=query) | Q(first_name__icontains=query) |
                             Q(last_name__icontains=query) | Q(email__icontains=query))
    return render(request, 'accounts/user_list.html', {'users': users, 'query': query})


@login_required
def user_create(request):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'receptionist')
        phone = request.POST.get('phone', '')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
                email=email, role=role, phone=phone
            )
            messages.success(request, f'User {username} created successfully!')
            return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'action': 'Create', 'roles': User.ROLE_CHOICES})


@login_required
def user_edit(request, pk):
    if not (request.user.role == 'admin' or request.user.is_superuser):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        user.phone = request.POST.get('phone', user.phone)
        user.is_active = 'is_active' in request.POST
        user.save()
        new_pass = request.POST.get('new_password')
        if new_pass:
            user.set_password(new_pass)
            user.save()
        messages.success(request, 'User updated successfully!')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {
        'action': 'Edit', 'edit_user': user, 'roles': User.ROLE_CHOICES
    })
