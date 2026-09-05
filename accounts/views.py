from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import UserRegistrationForm, UserProfileForm, LoginForm
from .utils import send_otp_email
from .models import User
from django.db import transaction

# Create your views here.
@transaction.atomic
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            # Password will be set in a later step.
            new_user.set_unusable_password()
            # Deactivate account until email is verified
            new_user.is_active = False
            new_user.save()
            send_otp_email(new_user)
            # Store user's pk in session to know who is verifying
            request.session['registration_user_id'] = new_user.pk
            return redirect('accounts:verify_otp')
        else:
            # This handles form validation errors.
            for error_list in user_form.errors.values():
                for error in error_list:
                    messages.error(request, error)
            return redirect('accounts:register')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'user_form': user_form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, email=cd['email'], password=cd['password'])
            if user is not None and user.is_active:
                login(request, user)                
                # On successful login, redirect to the main map page
                response = redirect('maps:main_map')
                # Set a simple, non-HttpOnly cookie that client-side JS can read
                response.set_cookie('is_logged_in', 'true', max_age=settings.SESSION_COOKIE_AGE)
                return response
            else:
                # This 'else' block will catch both 'user is None' (invalid credentials)
                # and 'user is not active'.
                messages.error(request, 'Invalid email or password.')
        else:
            # This handles cases where the form itself is invalid (e.g., bad email format)
            messages.error(request, 'Please enter a valid email and password.')
    
    # If login fails, redirect back to the homepage with a parameter to reopen the modal.
    # This also forces a page reload, which generates a fresh CSRF token.
    return redirect(f"{reverse('home')}?action=login")

def verify_email_sent(request):
    return render(request, 'accounts/verify_email_sent.html')

def verify_otp(request):
    user_id = request.session.get('registration_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please start the registration process again.')
        return redirect('accounts:register')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please start the registration process again.')
        return redirect('accounts:register')

    if request.method == 'POST':
        submitted_otp = request.POST.get('otp')
        if user.otp == submitted_otp and user.otp_expires_at > timezone.now():
            # OTP is valid and not expired
            user.is_active = True
            user.otp = None
            user.otp_expires_at = None
            user.save()
            
            # Log the user in to maintain the session for the next step
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return redirect('maps:main_map') # Redirect to the main map page after verification
        else:
            messages.error(request, 'The code you entered is invalid or has expired.')
    
    return render(request, 'accounts/verify_otp.html', {'user_email': user.email})

@login_required
def dashboard(request):
    if request.user.is_staff:
        return render(request, 'admin/dashboard.html', {'section': 'dashboard'})
    else:
        # For regular users, the map is the new dashboard/homepage.
        return redirect('maps:main_map')

def logout_view(request):
    logout(request)
    response = redirect('home')
    # Delete the flag cookie on logout to keep client-side state in sync
    response.delete_cookie('is_logged_in')
    return response
