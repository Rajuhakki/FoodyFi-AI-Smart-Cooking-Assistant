import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Recipe, Rating, Review

class RecipeModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Paneer Butter Masala",
            funny_title="The Butter Bomb",
            ingredients="Paneer, Butter, Tomatoes, Cream",
            content=json.dumps(["Cut paneer", "Make gravy", "Simmer 10 mins"]),
            fun_fact="Butter makes everything better!",
            language="English",
            image_url="https://example.com/paneer.jpg"
        )

    def test_recipe_creation(self):
        self.assertEqual(self.recipe.title, "Paneer Butter Masala")
        self.assertEqual(self.recipe.funny_title, "The Butter Bomb")
        self.assertEqual(self.recipe.language, "English")

    def test_average_rating_and_count(self):
        self.assertEqual(self.recipe.average_rating(), 0.0)
        self.assertEqual(self.recipe.ratings_count(), 0)

        Rating.objects.create(recipe=self.recipe, value=5)
        Rating.objects.create(recipe=self.recipe, value=3)

        self.assertEqual(self.recipe.average_rating(), 4.0)
        self.assertEqual(self.recipe.ratings_count(), 2)

    def test_steps_list(self):
        steps = self.recipe.steps_list()
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0], "Cut paneer")

    def test_ingredients_list(self):
        ing = self.recipe.ingredients_list()
        self.assertEqual(len(ing), 4)
        self.assertIn("Paneer", ing)


class RecipeViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.recipe = Recipe.objects.create(
            title="Spicy Egg Curry",
            funny_title="Egg-cellent Surprise",
            ingredients="Eggs, Onions, Spices",
            content=json.dumps(["Boil eggs", "Fry masala"]),
            language="English"
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FoodyFi")

    def test_recipe_detail_view(self):
        response = self.client.get(reverse('recipe_detail', args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Spicy Egg Curry")

    def test_cooking_mode_view(self):
        response = self.client.get(reverse('cooking_mode', args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Boil eggs")

    def test_search_view(self):
        response = self.client.get(reverse('search_recipes') + '?q=Egg')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Spicy Egg Curry")

