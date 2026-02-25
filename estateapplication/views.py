from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import mail_admins
from django.contrib.auth import login
from django.urls import reverse

from .models import Listing
from django.db.models import Q
from .forms import RegisterForm, InquiryForm, ProfileForm
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from pathlib import Path
import os

import json


def listing_list(request):
	qs = Listing.objects.filter(published=True, sold=False).order_by('-created_at')
	category = request.GET.get('category')
	q = request.GET.get('q')
	if category:
		qs = qs.filter(category=category)
	if q:
		qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
	return render(request, 'estateapplication/listing_list.html', {'listings': qs})


def listing_detail(request, pk):
	listing = get_object_or_404(Listing, pk=pk)
	if not listing.published and not request.user.is_staff:
		return redirect('listing_list')
	form = InquiryForm()
	return render(request, 'estateapplication/listing_detail.html', {'listing': listing, 'form': form})


def register(request):
	if request.method == 'POST':
		form = RegisterForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Registration successful. Welcome email sent.')
			return redirect('listing_list')
	else:
		form = RegisterForm()
	return render(request, 'estateapplication/register.html', {'form': form})


@login_required
def make_inquiry(request, pk):
	listing = get_object_or_404(Listing, pk=pk, published=True, sold=False)
	if request.method == 'POST':
		form = InquiryForm(request.POST)
		if form.is_valid():
			inquiry = form.save(commit=False)
			inquiry.listing = listing
			inquiry.user = request.user
			inquiry.save()
			# notify admins
			subject = f'New inquiry for {listing.title}'
			message = f'User: {request.user.get_username()}\nEmail: {request.user.email}\n\nMessage:\n{inquiry.message}'
			try:
				mail_admins(subject, message, fail_silently=True)
			except Exception:
				pass
			messages.success(request, 'Inquiry sent to administrators.')
			return redirect('listing_detail', pk=pk)
	else:
		form = InquiryForm()
	return render(request, 'estateapplication/inquiry_form.html', {'form': form, 'listing': listing})


@login_required
def pay_listing(request, pk):
	listing = get_object_or_404(Listing, pk=pk, published=True, sold=False)
	if request.method == 'POST':
		# In a real app integrate payment gateway here. For now mark as sold.
		listing.sold = True
		listing.owner = request.user
		listing.save()
		# notify admins
		try:
			mail_admins(f'Listing paid: {listing.title}', f'{request.user.get_username()} bought {listing.title}', fail_silently=True)
		except Exception:
			pass
		messages.success(request, 'Payment recorded. Listing is no longer available.')
		return redirect('listing_detail', pk=pk)
	return render(request, 'estateapplication/pay_confirm.html', {'listing': listing})


@login_required
def start_payment(request, pk):
	"""Create a fake payment session and render a stub payment provider page.

	The stub will POST to `pay_listing` to simulate a successful payment.
	"""
	listing = get_object_or_404(Listing, pk=pk, published=True, sold=False)
	# Create a fake session id and store minimal info in Django session
	session_id = get_random_string(16)
	request.session['payment_stub'] = {
		'session_id': session_id,
		'listing_id': listing.pk,
		'amount': str(listing.price),
	}
	return render(request, 'estateapplication/payment_provider.html', {'listing': listing, 'session_id': session_id})


# Staff-only: list saved email files
@staff_member_required
def email_list(request):
	email_dir = Path(settings.BASE_DIR) / 'tmp' / 'emails'
	files = []
	if email_dir.exists():
		for p in sorted(email_dir.iterdir(), key=os.path.getmtime, reverse=True):
			if p.is_file():
				files.append({'name': p.name, 'mtime': p.stat().st_mtime, 'size': p.stat().st_size})
	return render(request, 'estateapplication/email_list.html', {'files': files})


# Staff-only: view a single email file
@staff_member_required
def email_detail(request, filename):
	# prevent path traversal
	if '..' in filename or '/' in filename or '\\' in filename:
		return redirect('email_list')
	email_path = Path(settings.BASE_DIR) / 'tmp' / 'emails' / filename
	if not email_path.exists() or not email_path.is_file():
		return redirect('email_list')
	content = email_path.read_text(encoding='utf-8', errors='replace')
	return render(request, 'estateapplication/email_detail.html', {'filename': filename, 'content': content})


@login_required
def profile_update(request):
	profile = getattr(request.user, 'profile', None)
	if request.method == 'POST':
		form = ProfileForm(request.POST, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, 'Profile updated.')
			return redirect('listing_list')
	else:
		form = ProfileForm(instance=profile)
	return render(request, 'estateapplication/profile_form.html', {'form': form})


@login_required
def paystack_start(request, pk):
	listing = get_object_or_404(Listing, pk=pk, published=True, sold=False)
	secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
	if not secret:
		messages.error(request, 'Payment gateway not configured.')
		return redirect('listing_detail', pk=pk)

	# Prepare initialization payload
	callback_url = request.build_absolute_uri(reverse('paystack_callback'))
	amount_kobo = int(listing.price * 100)
	payload = {
		'email': request.user.email or '',
		'amount': amount_kobo,
		'reference': get_random_string(12),
		'callback_url': callback_url,
		'metadata': {'listing_id': listing.pk}
	}
	headers = {
		'Authorization': f'Bearer {secret}',
		'Content-Type': 'application/json'
	}
	try:
		resp = requests.post('https://api.paystack.co/transaction/initialize', data=json.dumps(payload), headers=headers, timeout=15)
		data = resp.json()
	except Exception as exc:
		messages.error(request, f'Error contacting Paystack: {exc}')
		return redirect('listing_detail', pk=pk)

	if not data.get('status'):
		messages.error(request, 'Failed to start payment. ' + data.get('message', ''))
		return redirect('listing_detail', pk=pk)

	auth_url = data['data'].get('authorization_url')
	ref = data['data'].get('reference')

	# Store mapping in session to verify later
	request.session[f'paystack_{ref}'] = {'listing_id': listing.pk, 'user_id': request.user.pk}
	return redirect(auth_url)


@login_required
def paystack_callback(request):
	# Paystack will redirect here with ?reference=...
	reference = request.GET.get('reference')
	if not reference:
		messages.error(request, 'No payment reference provided.')
		return redirect('listing_list')

	secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
	if not secret:
		messages.error(request, 'Payment gateway not configured.')
		return redirect('listing_list')

	headers = {'Authorization': f'Bearer {secret}'}
	try:
		resp = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers, timeout=15)
		data = resp.json()
	except Exception as exc:
		messages.error(request, f'Error verifying payment: {exc}')
		return redirect('listing_list')

	if not data.get('status') or data.get('data', {}).get('status') != 'success':
		messages.error(request, 'Payment not successful.')
		return redirect('listing_list')

	# retrieve session mapping
	mapping = request.session.get(f'paystack_{reference}')
	listing_id = None
	user_id = None
	if mapping:
		listing_id = mapping.get('listing_id')
		user_id = mapping.get('user_id')

	# fallback to metadata if present
	if not listing_id:
		listing_id = data.get('data', {}).get('metadata', {}).get('listing_id')

	if not listing_id:
		messages.error(request, 'Could not determine which listing this payment is for.')
		return redirect('listing_list')

	listing = get_object_or_404(Listing, pk=listing_id)
	# mark as sold and assign owner (use logged-in user if matches session)
	listing.sold = True
	try:
		listing.owner = request.user
	except Exception:
		pass
	listing.save()

	messages.success(request, 'Payment verified. Listing marked as sold.')
	return redirect('listing_detail', pk=listing.pk)
