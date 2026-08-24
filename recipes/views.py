import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Recipe, Rating, Review
from .ai_services import detect_ingredients_from_image, generate_recipe_ai, generate_food_image_ai, ask_voice_chef_ai
from .mongo import create_user, verify_user, get_user_by_username, update_user_profile

def login_required_custom(view_func):
    """
    Decorator/helper to require MongoDB login for views.
    """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('mongo_user'):
            messages.warning(request, "Please log in or register an account to access FoodyFi.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required_custom
def home_view(request):
    """
    Renders the homepage with input form, voice/image options, 
    multi-language selector, smart ingredient chips, and recent recipes.
    """
    recent_recipes = Recipe.objects.all()[:6]
    smart_chips = [
        "Paneer", "Tomatoes", "Garlic", "Onions", "Chicken",
        "Spinach", "Cheese", "Rice", "Eggs", "Potatoes",
        "Bell Peppers", "Butter", "Capsicum", "Green Chilies"
    ]
    return render(request, 'recipes/home.html', {
        'recent_recipes': recent_recipes,
        'smart_chips': smart_chips
    })

@require_POST
@login_required_custom
def detect_ingredients_api(request):
    """
    AJAX endpoint to receive an uploaded image and return AI-detected ingredients.
    """
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image file uploaded'}, status=400)
    
    image_file = request.FILES['image']
    image_bytes = image_file.read()
    
    detected = detect_ingredients_from_image(image_bytes)
    return JsonResponse({
        'success': True,
        'ingredients': detected
    })

@require_POST
@login_required_custom
def generate_recipe_view(request):
    """
    POST endpoint that takes ingredients and selected language, calls AI to generate 3 recipe options,
    saves all 3 in DB, and redirects to the Result/Detail view displaying options.
    """
    ingredients_text = request.POST.get('ingredients', '').strip()
    language = request.POST.get('language', 'English')
    dietary_list = request.POST.getlist('dietary')
    is_zero_waste = request.POST.get('zero_waste') == 'true'
    
    if not ingredients_text:
        return redirect('home')

    # 1. Call AI to generate 3 structured recipe options
    ai_recipes = generate_recipe_ai(ingredients_text, language, dietary_list=dietary_list, is_zero_waste=is_zero_waste)
    if isinstance(ai_recipes, dict):
        ai_recipes = [ai_recipes]

    created_recipes = []
    for item in ai_recipes:
        image_url = generate_food_image_ai(item['title'])
        recipe = Recipe.objects.create(
            title=item['title'],
            funny_title=item.get('funny_title', ''),
            ingredients=json.dumps(item['ingredients']) if isinstance(item['ingredients'], list) else str(item['ingredients']),
            content=json.dumps(item['steps']) if isinstance(item['steps'], list) else str(item['steps']),
            fun_fact=item.get('fun_fact', ''),
            language=language,
            image_url=image_url,
            youtube_query=item.get('youtube_query', f"{item['title']} recipe video tutorial"),
            youtube_video_id=item.get('youtube_video_id', ''),
            prep_time=item.get('prep_time', '25 mins'),
            difficulty=item.get('difficulty', 'Medium'),
            nutrition=json.dumps(item.get('nutrition', {})) if isinstance(item.get('nutrition'), dict) else str(item.get('nutrition', ''))
        )
        created_recipes.append(recipe)

    batch_ids_str = ",".join(str(r.id) for r in created_recipes)
    first_id = created_recipes[0].id if created_recipes else 1
    return redirect(f"/recipe/{first_id}/?batch={batch_ids_str}")

@require_POST
@login_required_custom
def ask_voice_chef_api(request):
    """
    AJAX endpoint for AI Voice Chef Assistant questions during cooking.
    """
    question = request.POST.get('question', '').strip()
    recipe_title = request.POST.get('recipe_title', '').strip()
    ingredients = request.POST.get('ingredients', '').strip()
    current_step = request.POST.get('current_step', '').strip()

    if not question:
        return JsonResponse({'error': 'Question cannot be empty'}, status=400)

    answer = ask_voice_chef_ai(question, recipe_title, ingredients, current_step)
    return JsonResponse({
        'success': True,
        'answer': answer
    })

@login_required_custom
def recipe_detail_view(request, recipe_id):
    """
    Renders the result page displaying the generated recipe, YouTube video tutorial,
    3 alternative suggested options, funny name, fun fact, ratings, review form, and cooking mode.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    reviews = recipe.reviews.all()
    avg_rating = recipe.average_rating()
    ratings_count = recipe.ratings_count()
    
    batch_str = request.GET.get('batch', '').strip()
    other_options = []
    if batch_str:
        try:
            b_ids = [int(x) for x in batch_str.split(',') if x.isdigit()]
            other_options = list(Recipe.objects.filter(id__in=b_ids))
        except Exception:
            other_options = []

    if not other_options:
        # Fallback to recent recipes
        other_options = list(Recipe.objects.all()[:3])
    
    return render(request, 'recipes/result.html', {
        'recipe': recipe,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'ratings_count': ratings_count,
        'steps': recipe.steps_list(),
        'ingredients_list': recipe.ingredients_list(),
        'other_options': other_options,
        'batch_str': batch_str
    })

@login_required_custom
def cooking_mode_view(request, recipe_id):
    """
    Interactive Step-by-Step Cooking Assistant page.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    steps = recipe.steps_list()
    
    # Store session state for cooking mode
    request.session['current_recipe_id'] = recipe.id
    
    return render(request, 'recipes/cooking_mode.html', {
        'recipe': recipe,
        'steps': steps,
        'steps_json': json.dumps(steps)
    })

@require_POST
@login_required_custom
def rate_recipe_view(request, recipe_id):
    """
    AJAX/POST endpoint to add a rating (1-5 stars) to a recipe.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    try:
        val = int(request.POST.get('value', 5))
        if 1 <= val <= 5:
            Rating.objects.create(recipe=recipe, value=val)
            return JsonResponse({
                'success': True,
                'avg_rating': recipe.average_rating(),
                'ratings_count': recipe.ratings_count()
            })
    except (ValueError, TypeError):
        pass
    
    return JsonResponse({'error': 'Invalid rating value'}, status=400)

@require_POST
@login_required_custom
def add_review_view(request, recipe_id):
    """
    POST endpoint to add a user comment/review.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    comment = request.POST.get('comment', '').strip()
    
    if comment:
        Review.objects.create(recipe=recipe, comment=comment)
        
    return redirect('recipe_detail', recipe_id=recipe.id)

@login_required_custom
def search_recipes_view(request):
    """
    Search recipes by title or ingredients keyword.
    """
    query = request.GET.get('q', '').strip()
    recipes = []
    if query:
        recipes = Recipe.objects.filter(
            Q(title__icontains=query) | 
            Q(funny_title__icontains=query) | 
            Q(ingredients__icontains=query)
        )
    else:
        recipes = Recipe.objects.all()

    return render(request, 'recipes/search.html', {
        'query': query,
        'recipes': recipes
    })

# ================================
# MongoDB Authentication Views
# ================================

def register_view(request):
    """
    User registration view saving user details into MongoDB.
    After successful registration, redirects to the Login page.
    """
    if request.session.get('mongo_user'):
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validations
        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'recipes/register.html', {
                'full_name': full_name, 'username': username, 'email': email
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'recipes/register.html', {
                'full_name': full_name, 'username': username, 'email': email
            })

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'recipes/register.html', {
                'full_name': full_name, 'username': username, 'email': email
            })

        try:
            success, result = create_user(username=username, email=email, password=password, full_name=full_name)
            if success:
                messages.success(request, f"Account for '{username}' created successfully in MongoDB! Please log in to continue.")
                return redirect('login')
            else:
                messages.error(request, result)
                return render(request, 'recipes/register.html', {
                    'full_name': full_name, 'username': username, 'email': email
                })
        except Exception as e:
            messages.error(request, f"Database error: {str(e)}")
            return render(request, 'recipes/register.html', {
                'full_name': full_name, 'username': username, 'email': email
            })

    return render(request, 'recipes/register.html')

def login_view(request):
    """
    User login view verifying credentials against MongoDB.
    Once authenticated, user can access all application pages.
    """
    if request.session.get('mongo_user'):
        return redirect('home')

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        if not identifier or not password:
            messages.error(request, "Please enter your username/email and password.")
            return render(request, 'recipes/login.html', {'identifier': identifier})

        try:
            user_doc, error = verify_user(identifier, password)
            if user_doc:
                request.session['mongo_user'] = {
                    'id': user_doc['_id'],
                    'username': user_doc['username'],
                    'email': user_doc['email'],
                    'full_name': user_doc.get('full_name', '')
                }
                messages.success(request, f"Welcome to FoodyFi, {user_doc['username']}!")
                return redirect('home')
            else:
                messages.error(request, error or "Authentication failed.")
                return render(request, 'recipes/login.html', {'identifier': identifier})
        except Exception as e:
            messages.error(request, f"Unable to connect to MongoDB: {str(e)}")
            return render(request, 'recipes/login.html', {'identifier': identifier})

    return render(request, 'recipes/login.html')

def logout_view(request):
    """
    Logs out the current session user and redirects to login page.
    """
    if 'mongo_user' in request.session:
        del request.session['mongo_user']
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required_custom
def profile_view(request):
    """
    User Profile view showing user data fetched from MongoDB and allowing edits.
    """
    session_user = request.session.get('mongo_user')
    try:
        user_doc = get_user_by_username(session_user['username'])
    except Exception:
        user_doc = None

    if not user_doc:
        messages.error(request, "User record not found in database or database unavailable.")
        return redirect('logout')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        bio = request.POST.get('bio', '').strip()
        favorite_cuisine = request.POST.get('favorite_cuisine', '').strip()

        ok, msg = update_user_profile(user_doc['username'], full_name, bio, favorite_cuisine)
        if ok:
            # Update session info if full_name changed
            request.session['mongo_user']['full_name'] = full_name
            request.session.modified = True
            messages.success(request, msg)
            user_doc = get_user_by_username(session_user['username'])
        else:
            messages.error(request, msg)

    return render(request, 'recipes/profile.html', {'user_doc': user_doc})



