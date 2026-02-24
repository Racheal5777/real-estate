from django.db import models
from django.conf import settings
from django.utils import timezone


class Listing(models.Model):
	CATEGORY_SALE = 'sale'
	CATEGORY_RENT = 'rent'
	CATEGORY_BUY = 'buy'
	CATEGORY_CHOICES = [
		(CATEGORY_SALE, 'Sale'),
		(CATEGORY_RENT, 'Rent'),
		(CATEGORY_BUY, 'Buy'),
	]

	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
	price = models.DecimalField(max_digits=12, decimal_places=2)
	published = models.BooleanField(default=False)
	sold = models.BooleanField(default=False)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.title} ({self.get_category_display()})"


class Inquiry(models.Model):
	listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='inquiries')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self):
		user = self.user.email if self.user else 'Anonymous'
		return f"Inquiry by {user} for {self.listing.title}"


class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	phone = models.CharField(max_length=30, blank=True)
	bio = models.TextField(blank=True)

	def __str__(self):
		return f"Profile for {self.user.get_username()}"



class Photo(models.Model):
	listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='photos')
	image = models.ImageField(upload_to='listing_photos/')
	caption = models.CharField(max_length=200, blank=True)
	order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ['order', 'id']

	def __str__(self):
		return f"Photo for {self.listing.title} ({self.pk})"
