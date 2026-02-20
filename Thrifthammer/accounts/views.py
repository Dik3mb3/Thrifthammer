from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ForgotPasswordStep1Form, ForgotPasswordStep2Form, RegistrationForm
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
    """Show the user's profile with a summary of their watchlist."""
    watchlist = request.user.watchlist_items.select_related('product').all()
    return render(request, 'accounts/profile.html', {'watchlist': watchlist})


@login_required
def watchlist(request):
    """
    Show all products the user is watching, with current prices and alerts.

    Annotates each item with a price_dropped flag when the current best
    price is below the user's target price.
    """
    items = (
        WatchlistItem.objects
        .filter(user=request.user)
        .select_related('product', 'product__category', 'product__faction')
        .prefetch_related('product__current_prices__retailer')
        .order_by('-created_at')
    )

    # Annotate each item with current best price and price-drop flag
    enriched = []
    for item in items:
        best = item.product.get_cheapest_price()
        price_dropped = (
            best is not None
            and item.target_price is not None
            and best.price < item.target_price
        )
        enriched.append({
            'item': item,
            'best': best,
            'price_dropped': price_dropped,
        })

    return render(request, 'accounts/watchlist.html', {
        'enriched': enriched,
        'total': len(enriched),
    })


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
        # Neutral message to prevent username enumeration
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
        profile = user.security_profile
    except SecurityProfile.DoesNotExist:
        messages.error(request, 'No security question found for this account.')
        return redirect('accounts:forgot_password')

    question_text = dict(SecurityProfile.QUESTIONS).get(profile.question, profile.question)
    form = ForgotPasswordStep2Form(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        raw_answer = form.cleaned_data['security_answer']
        if not profile.check_answer(raw_answer):
            messages.error(request, 'Incorrect security answer. Please try again.')
        else:
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # keep user logged in if they were
            del request.session['pw_reset_user_id']
            messages.success(request, 'Password updated successfully. You can now log in.')
            return redirect('accounts:login')

    return render(request, 'accounts/forgot_password_step2.html', {
        'form': form,
        'question': question_text,
        'username': user.username,
    })
