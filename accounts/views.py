from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
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
    watchlist = request.user.watchlist_items.select_related('product').all()
    return render(request, 'accounts/profile.html', {'watchlist': watchlist})
