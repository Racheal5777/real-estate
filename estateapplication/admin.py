from django.contrib import admin
from django.utils.html import format_html
from django.forms import ClearableFileInput
from .models import Listing, Inquiry, Profile, Photo


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
	list_display = ('listing', 'user', 'created_at')
	search_fields = ('listing__title', 'user__email', 'message')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'phone')


class PhotoInline(admin.TabularInline):
	model = Photo
	extra = 1


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
	list_display = ('listing', 'thumbnail', 'caption', 'order')
	readonly_fields = ('thumbnail',)

	def thumbnail(self, obj):
		if obj.image:
			return format_html('<img src="{}" style="max-height:60px;"/>', obj.image.url)
		return ''
	thumbnail.short_description = 'Image'


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'price', 'published', 'sold', 'owner', 'created_at')
	list_filter = ('category', 'published', 'sold')
	search_fields = ('title', 'description')
	inlines = [PhotoInline]
