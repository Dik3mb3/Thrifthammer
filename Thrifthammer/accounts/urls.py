from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/change-email/', views.change_email, name='change_email'),
    path('profile/change-username/', views.change_username, name='change_username'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/<int:item_id>/alert/', views.update_watchlist_alert, name='update_watchlist_alert'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'),
        name='password_change',
    ),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done',
    ),
    # Newsletter opt-in / opt-out toggle (POST only)
    path('profile/newsletter-toggle/', views.toggle_newsletter, name='newsletter_toggle'),
    # Newsletter preferences update (POST only — checkboxes + faction multi-select)
    path('profile/newsletter-prefs/', views.update_newsletter_prefs, name='newsletter_prefs'),
    # Email-based password reset (Django built-in, 4-step flow)
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done'),
    ), name='forgot_password'),
    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('forgot-password/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('forgot-password/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
]
