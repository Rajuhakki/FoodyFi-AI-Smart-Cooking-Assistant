from django.contrib import admin
from .models import Recipe, Rating, Review

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'funny_title', 'language', 'average_rating', 'ratings_count', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('title', 'funny_title', 'ingredients', 'content')
    readonly_fields = ('created_at',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('recipe__title',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'short_comment', 'created_at')
    search_fields = ('recipe__title', 'comment')
    list_filter = ('created_at',)

    def short_comment(self, obj):
        return obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
    short_comment.short_description = 'Comment'

