from django.contrib import admin
from .models import Post

class PostAdmin(admin.ModelAdmin):
    list_display = ("id",)

admin.site.register(Post, PostAdmin)
