from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('detect-ingredients/', views.detect_ingredients_api, name='detect_ingredients_api'),
    path('generate/', views.generate_recipe_view, name='generate_recipe'),
    path('recipe/<int:recipe_id>/', views.recipe_detail_view, name='recipe_detail'),
    path('recipe/<int:recipe_id>/cooking/', views.cooking_mode_view, name='cooking_mode'),
    path('recipe/<int:recipe_id>/rate/', views.rate_recipe_view, name='rate_recipe'),
    path('recipe/<int:recipe_id>/review/', views.add_review_view, name='add_review'),
    path('search/', views.search_recipes_view, name='search_recipes'),
    
    # MongoDB User Authentication Routes
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]

