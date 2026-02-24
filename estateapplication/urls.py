from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
	path('', views.listing_list, name='listing_list'),
	path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),
	path('inquire/<int:pk>/', views.make_inquiry, name='make_inquiry'),
	path('pay/<int:pk>/', views.pay_listing, name='pay_listing'),
	path('pay/start/<int:pk>/', views.start_payment, name='start_payment'),
	path('profile/', views.profile_update, name='profile_update'),
	path('register/', views.register, name='register'),
	path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
	path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
	path('emails/', views.email_list, name='email_list'),
	path('emails/<str:filename>/', views.email_detail, name='email_detail'),
	path('pay/paystack/<int:pk>/', views.paystack_start, name='paystack_start'),
	path('pay/paystack/callback/', views.paystack_callback, name='paystack_callback'),
]