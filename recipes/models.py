import json
from django.db import models
from django.db.models import Avg

class Recipe(models.Model):
    title = models.CharField(max_length=255)
    funny_title = models.CharField(max_length=255, blank=True, default='')
    ingredients = models.TextField(help_text="Raw or comma-separated list of ingredients")
    content = models.TextField(help_text="Step-by-step instructions or JSON string")
    fun_fact = models.TextField(blank=True, default='')
    language = models.CharField(max_length=30, default='English')
    image_url = models.TextField(blank=True, default='')
    youtube_query = models.CharField(max_length=255, blank=True, default='')
    youtube_video_id = models.CharField(max_length=50, blank=True, default='')
    prep_time = models.CharField(max_length=50, default='25 mins')
    difficulty = models.CharField(max_length=50, default='Medium')
    nutrition = models.TextField(blank=True, default='', help_text="JSON string of calorie and macro metrics")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.language})"

    def nutrition_dict(self):
        """Returns nutrition data as a dictionary with defaults if empty."""
        if self.nutrition:
            try:
                data = json.loads(self.nutrition)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {
            "calories": "360 kcal",
            "protein": "16g",
            "carbs": "28g",
            "fat": "18g",
            "health_score": "8.8/10",
            "health_badge": "Balanced & Protein Rich"
        }

    def get_youtube_embed_url(self):
        if not self.youtube_video_id and (self.youtube_query or self.title):
            from .ai_services import fetch_youtube_video_id
            query = self.youtube_query or f"{self.title} recipe tutorial"
            vid = fetch_youtube_video_id(query)
            if vid:
                self.youtube_video_id = vid
                try:
                    self.save(update_fields=['youtube_video_id'])
                except Exception:
                    pass

        if self.youtube_video_id:
            return f"https://www.youtube-nocookie.com/embed/{self.youtube_video_id}?rel=0&modestbranding=1"

        import urllib.parse
        query = self.youtube_query or f"{self.title} recipe tutorial"
        return f"https://www.youtube-nocookie.com/embed?listType=search&list={urllib.parse.quote(query)}"

    def get_youtube_search_url(self):
        query = self.youtube_query or f"{self.title} recipe tutorial"
        import urllib.parse
        return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    def average_rating(self):
        avg = self.ratings.aggregate(Avg('value'))['value__avg']
        return round(avg, 1) if avg is not None else 0.0

    def ratings_count(self):
        return self.ratings.count()

    def steps_list(self):
        """Parse steps from JSON or newline-separated text content."""
        if not self.content:
            return []
        try:
            data = json.loads(self.content)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "steps" in data:
                return data["steps"]
        except Exception:
            pass
        # Fallback split by newline or numbered list
        lines = [line.strip() for line in self.content.split('\n') if line.strip()]
        return lines

    def ingredients_list(self):
        """Return ingredients formatted as a clean Python list."""
        if not self.ingredients:
            return []
        try:
            data = json.loads(self.ingredients)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        # Split by comma or newline
        items = [i.strip('- ').strip() for i in self.ingredients.replace('\n', ',').split(',') if i.strip()]
        return items


class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    value = models.IntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.value} Stars for {self.recipe.title}"


class Review(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review on {self.recipe.title}: {self.comment[:30]}"

