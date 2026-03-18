from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    ChangeEmailForm,
    ChangeUsernameForm,
    DeleteAccountForm,
    ForgotPasswordStep1Form,
    ForgotPasswordStep2Form,
    RegistrationForm,
    WatchlistAlertForm,
)
from .models import SecurityProfile, WatchlistItem


def register(request):
    """Register a new user account, including a security question for password recovery."""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! You can now log in.')
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """
    User account settings page.

    Shows email/username/password change forms and the delete-account option.
    The watchlist lives on its own separate page.
    """
    email_form = ChangeEmailForm(request.user)
    username_form = ChangeUsernameForm(request.user)

    return render(request, 'accounts/profile.html', {
        'email_form': email_form,
        'username_form': username_form,
    })


@login_required
def change_email(request):
    """POST-only: update the user's email address after password verification."""
    if request.method != 'POST':
        return redirect('accounts:profile')
    form = ChangeEmailForm(request.user, request.POST)
    if form.is_valid():
        request.user.email = form.cleaned_data['new_email']
        request.user.save(update_fields=['email'])
        messages.success(request, 'Email address updated.')
        return redirect('accounts:profile')
    # Re-render profile with this form's errors
    return render(request, 'accounts/profile.html', {
        'email_form': form,
        'username_form': ChangeUsernameForm(request.user),
        'open_section': 'email',
    })


@login_required
def change_username(request):
    """POST-only: update the user's username after password verification."""
    if request.method != 'POST':
        return redirect('accounts:profile')
    form = ChangeUsernameForm(request.user, request.POST)
    if form.is_valid():
        request.user.username = form.cleaned_data['new_username']
        request.user.save(update_fields=['username'])
        messages.success(request, 'Username updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {
        'email_form': ChangeEmailForm(request.user),
        'username_form': form,
        'open_section': 'username',
    })


@login_required
def delete_account(request):
    """
    Two-step account deletion.

    GET  → show confirmation page.
    POST → verify password, then delete the user and all related data.
    """
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account and all data have been permanently deleted.')
            return redirect('products:home')
        return render(request, 'accounts/delete_account.html', {'form': form})
    form = DeleteAccountForm(request.user)
    return render(request, 'accounts/delete_account.html', {'form': form})


@login_required
def watchlist(request):
    """
    Show all products the user is watching, with current prices and alert config.
    """
    items = (
        WatchlistItem.objects
        .filter(user=request.user)
        .select_related('product', 'product__category', 'product__faction')
        .prefetch_related('product__current_prices__retailer')
        .order_by('-created_at')
    )

    enriched = []
    for item in items:
        best = item.product.get_cheapest_price()
        price_dropped = (
            best is not None
            and item.target_price is not None
            and best.price <= item.target_price
        )
        alert_triggered = item.alert_condition_met(best)
        enriched.append({
            'item': item,
            'best': best,
            'price_dropped': price_dropped,
            'alert_triggered': alert_triggered,
            'alert_form': WatchlistAlertForm(instance=item),
        })

    return render(request, 'accounts/watchlist.html', {
        'enriched': enriched,
        'total': len(enriched),
    })


@login_required
@require_POST
def update_watchlist_alert(request, item_id):
    """Update the email alert configuration for a single watchlist item."""
    item = get_object_or_404(WatchlistItem, pk=item_id, user=request.user)
    form = WatchlistAlertForm(request.POST, instance=item)
    if form.is_valid():
        # Reset the last_alerted_price so a fresh alert can fire
        updated = form.save(commit=False)
        updated.last_alerted_price = None
        updated.save()
        messages.success(request, f'Alert updated for {item.product.name}.')
    else:
        for error in form.errors.values():
            messages.error(request, error.as_text())
    return redirect('accounts:watchlist')


def forgot_password(request):
    """
    Step 1 of self-service password reset.

    The user enters their username. If an account exists and has a security
    profile, we store the username in the session and redirect to step 2.
    We show a neutral error for both 'not found' and 'no security question'
    to avoid username enumeration.
    """
    form = ForgotPasswordStep1Form(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username'].strip()
        user = User.objects.filter(username__iexact=username).first()
        if user and hasattr(user, 'security_profile'):
            request.session['pw_reset_user_id'] = user.pk
            return redirect('accounts:forgot_password_verify')
        messages.error(request, 'No account found with that username, or no security question set.')

    return render(request, 'accounts/forgot_password_step1.html', {'form': form})


def forgot_password_verify(request):
    """
    Step 2 of self-service password reset.

    Retrieves the user from the session, shows the security question, and
    verifies the answer. On success, sets a new password and clears the session.
    """
    user_id = request.session.get('pw_reset_user_id')
    if not user_id:
        return redirect('accounts:forgot_password')

    user = get_object_or_404(User, pk=user_id)
    try:
        profile_obj = user.security_profile
    except SecurityProfile.DoesNotExist:
        messages.error(request, 'No security question found for this account.')
        return redirect('accounts:forgot_password')

    question_text = dict(SecurityProfile.QUESTIONS).get(profile_obj.question, profile_obj.question)
    form = ForgotPasswordStep2Form(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        raw_answer = form.cleaned_data['security_answer']
        if not profile_obj.check_answer(raw_answer):
            messages.error(request, 'Incorrect security answer. Please try again.')
        else:
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            del request.session['pw_reset_user_id']
            messages.success(request, 'Password updated successfully. You can now log in.')
            return redirect('accounts:login')

    return render(request, 'accounts/forgot_password_step2.html', {
        'form': form,
        'question': question_text,
        'username': user.username,
    })
