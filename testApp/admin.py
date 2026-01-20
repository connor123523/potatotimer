from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "short_content", "created_at")
    list_filter = ("author", "created_at")
    search_fields = ("content", "author__username")

    @admin.display(description="Content")
    def short_content(self, obj):
        return obj.content[:20] + ("..." if len(obj.content) > 20 else "")