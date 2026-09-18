from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import (
    Category,
    Faction,
    NewsletterSignup,
    NON_GAME_SYSTEM_CATEGORY_SLUGS,
    WARHAMMER_CATEGORY_SLUGS,
)

from .forms import (
    ChangeEmailForm,
    ChangeUsernameForm,
    DeleteAccountForm,
    RegistrationForm,
    WatchlistAlertForm,
)
from .models import WatchlistItem


def register(request):
    """
    Register a new user account, including a security question for password recovery.

    Automatically subscribes the new user to Monday 40K and Friday AoS newsletters
    using their registration email. Confirmed immediately (no opt-in email needed —
    the user just provided the email themselves).
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data['email'].strip().lower()
            if email:
                # Region default comes from the current browsing-session value,
                # same as the homepage/blog signup forms. Only used on the
                # CREATE path below -- if this email already has a signup
                # (e.g. from a homepage signup), their region choice from
                # that earlier signup is left as-is, not silently overridden.
                session_region = request.session.get('region', NewsletterSignup.REGION_US)
                if session_region not in dict(NewsletterSignup.REGION_CHOICES):
                    session_region = NewsletterSignup.REGION_US

                signup, created = NewsletterSignup.objects.get_or_create(
                    email=email,
                    defaults={
                        'user': user,
                        'is_confirmed': True,
                        'monday_40k': True,
                        'friday_other': True,
                        'sunday_faction': False,
                        'region': session_region,
                    },
                )
                if not created:
                    # Email already existed (e.g. homepage signup) — link the account
                    signup.user = user
                    signup.is_confirmed = True
                    signup.save(update_fields=['user', 'is_confirmed'])
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
    Also shows a newsletter opt-in/out toggle based on whether the user's
    email address is in the NewsletterSignup table.
    """
    email_form = ChangeEmailForm(request.user)
    username_form = ChangeUsernameForm(request.user)

    newsletter_obj = None
    newsletter_subscribed = False
    if request.user.email:
        newsletter_obj = (
            NewsletterSignup.objects
            .filter(email__iexact=request.user.email)
            .prefetch_related('factions')
            .first()
        )
        newsletter_subscribed = newsletter_obj is not None

    all_factions = Faction.objects.select_related('category').order_by('category__name', 'name')
    all_categories = Category.objects.order_by('name')

    return render(request, 'accounts/profile.html', {
        'email_form': email_form,
        'username_form': username_form,
        'newsletter_subscribed': newsletter_subscribed,
        'newsletter_obj': newsletter_obj,
        'all_factions': all_factions,
        'all_categories': all_categories,
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


@login_required
@require_POST
def toggle_newsletter(request):
    """
    POST-only: subscribe or unsubscribe the logged-in user from weekly deal emails.

    Uses the user's account email as the key in NewsletterSignup. If they have
    no email set we redirect back with an error asking them to add one first.
    """
    email = request.user.email.strip().lower() if request.user.email else ''
    if not email:
        messages.error(request, 'Add an email address to your account before subscribing to deal alerts.')
        return redirect('accounts:profile')

    existing = NewsletterSignup.objects.filter(email__iexact=email).first()
    if existing:
        existing.delete()
        messages.success(request, 'You have been unsubscribed from weekly deal alerts.')
    else:
        # Profile subscribers are already authenticated — confirm immediately,
        # no confirmation email needed. Region defaults from the current
        # browsing session, same as every other signup entry point; they
        # can correct it with the region control further down this page.
        session_region = request.session.get('region', NewsletterSignup.REGION_US)
        if session_region not in dict(NewsletterSignup.REGION_CHOICES):
            session_region = NewsletterSignup.REGION_US

        NewsletterSignup.objects.create(
            email=email,
            user=request.user,
            is_confirmed=True,
            region=session_region,
        )
        messages.success(request, "You're subscribed! We'll send you the best weekly deals every Wednesday.")

    return redirect('accounts:profile')


@login_required
@require_POST
def update_newsletter_prefs(request):
    """
    POST-only: update newsletter preferences for the logged-in subscriber.

    Handles region, monday_40k, friday_other, sunday_faction, monday_custom
    toggles and the faction / category multi-selects. Silently redirects if
    the user is not subscribed.
    """
    email = request.user.email.strip().lower() if request.user.email else ''
    signup = NewsletterSignup.objects.filter(email__iexact=email).first() if email else None

    if not signup:
        messages.error(request, 'You are not currently subscribed to deal alerts.')
        return redirect('accounts:profile')

    was_monday_custom = signup.monday_custom

    # One region controls currency/retailers for every digest below --
    # validated against the model's own choices, not trusted as raw POST input.
    region = request.POST.get('region', '').strip().lower()
    if region in dict(NewsletterSignup.REGION_CHOICES):
        signup.region = region

    signup.monday_40k = 'monday_40k' in request.POST
    signup.friday_other = 'friday_other' in request.POST
    signup.sunday_faction = 'sunday_faction' in request.POST
    signup.monday_custom = 'monday_custom' in request.POST

    # Faction multi-select — only integers, ignore bad input
    faction_ids = []
    for fid in request.POST.getlist('factions'):
        try:
            faction_ids.append(int(fid))
        except (ValueError, TypeError):
            pass

    # Category multi-select for the Monday Customized Game System digest —
    # only integers, ignore bad input.
    category_ids = []
    for cid in request.POST.getlist('custom_categories'):
        try:
            category_ids.append(int(cid))
        except (ValueError, TypeError):
            pass

    signup.save(update_fields=['region', 'monday_40k', 'friday_other', 'sunday_faction', 'monday_custom'])
    signup.factions.set(faction_ids)

    # First time turning Monday Custom on with nothing manually picked yet —
    # default to every non-Warhammer, actual-game-system category rather
    # than saving an empty selection (which would just make the digest skip
    # them every week). Only applies on the off->on transition; an explicit
    # later save with zero categories (turning everything off) is respected
    # as-is. Discount Box Splits / Paint & Supplies / Boxed Games are left
    # out of the default too -- not really "game systems" -- but remain
    # manually selectable.
    if signup.monday_custom and not was_monday_custom and not category_ids:
        category_ids = list(
            Category.objects
            .exclude(slug__in=WARHAMMER_CATEGORY_SLUGS | NON_GAME_SYSTEM_CATEGORY_SLUGS)
            .values_list('pk', flat=True)
        )

    signup.custom_categories.set(category_ids)

    messages.success(request, 'Newsletter preferences updated.')
    return redirect('accounts:profile')


