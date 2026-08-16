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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.language})"

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

