import os
import json
import base64
import random
import urllib.parse
import urllib.request
import re
from django.conf import settings

COMMON_RECIPE_VIDEO_MAP = {
    'chicken': 'a03U45jFxOI',
    'paneer': 'ckSdRrgnbQI',
    'butter masala': 'ckSdRrgnbQI',
    'masala': 'ckSdRrgnbQI',
    'soup': 'DUOfppgPHFU',
    'fry': 'DUOfppgPHFU',
    'tawa': 'DUOfppgPHFU',
    'curry': 'a03U45jFxOI',
}

def fetch_youtube_video_id(query):
    """
    Searches YouTube for the specific recipe query and returns the exact video ID.
    Handles network / DNS offline errors quietly with instant keyword fallbacks.
    """
    if not query:
        return ""

    q_lower = query.lower()

    # 1. Try online fetch with short timeout (1.5s)
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            match = re.search(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            if match:
                return match.group(1)
    except Exception:
        # Silently handle DNS / network connection errors without polluting console
        pass

    # 2. Instant offline keyword-matched video fallback
    for key, vid in COMMON_RECIPE_VIDEO_MAP.items():
        if key in q_lower:
            return vid

    return ""

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def get_openai_client():
    api_key = getattr(settings, 'OPENAI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')
    if api_key and OpenAI:
        try:
            return OpenAI(api_key=api_key)
        except Exception:
            return None
    return None

def detect_ingredients_from_image(image_bytes):
    """
    Uses OpenAI Vision API (GPT-4o or GPT-4o-mini) to detect food ingredients in an image.
    Falls back to smart mock detection if API key is not configured or error occurs.
    """
    client = get_openai_client()
    if client:
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Identify all raw or cooked food ingredients visible in this image. Return ONLY a comma-separated list of ingredient names in English. Do not add any extra text or intro."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
            )
            detected = response.choices[0].message.content.strip()
            if detected:
                return detected
        except Exception as e:
            print(f"OpenAI Vision error: {e}")

    # Fallback simulated vision detection
    mock_samples = [
        "Tomatoes, Garlic, Paneer, Bell Peppers, Onions, Olive Oil",
        "Potatoes, Green Peas, Cumin Seeds, Turmeric, Chili Powder, Ginger",
        "Eggs, Spinach, Cheese, Mushrooms, Black Pepper, Butter",
        "Rice, Soy Sauce, Carrots, Spring Onions, Garlic, Chicken"
    ]
    return random.choice(mock_samples)


def generate_recipe_ai(ingredients_text, language='English', dietary_list=None, is_zero_waste=False):
    """
    Generates 3 distinct recipe options with dietary preference enforcement & zero-waste fridge optimization.
    """
    client = get_openai_client()
    
    lang_prompt_map = {
        'Kannada': 'in Kannada language (written in Kannada script)',
        'Hindi': 'in Hindi language (written in Devanagari script)',
        'English': 'in English'
    }
    target_lang_str = lang_prompt_map.get(language, 'in English')

    dietary_str = f"MUST STRICTLY COMPLY WITH DIETARY REQUIREMENTS: {', '.join(dietary_list)}." if dietary_list else ""
    zero_waste_str = "ZERO-WASTE MODE: Focus on utilizing 100% of these available ingredients to eliminate food waste!" if is_zero_waste else ""

    prompt = f"""You are FoodyFi, a world-class AI Master Chef and culinary expert.
Based on these available ingredients: {ingredients_text}
{dietary_str}
{zero_waste_str}

Generate 3 DISTINCT, mouthwatering recipe suggestions (Option 1: Classic Gravy/Main Course, Option 2: Quick Stir Fry/Snack, Option 3: Creamy Soup/Special Fusion) {target_lang_str}.

FOR EACH RECIPE:
- Provide 6 to 8 highly detailed step-by-step cooking instructions with stove flame levels, precise minutes, and spice ratios.
- Include a specific YouTube video search query for finding video tutorials of this recipe in English or regional language.
- Include prep time (e.g., "25 mins") and difficulty level ("Easy", "Medium", "Chef Special").
- Include an AI estimated nutrition breakdown with calories, protein, carbs, fat, health_score (e.g. "8.5/10"), and health_badge (e.g. "High Protein & Balanced").

Return your response strictly in raw JSON format with a top-level key "recipes" containing an array of 3 recipe objects:
{{
  "recipes": [
    {{
      "title": "Recipe Title",
      "funny_title": "Humorous nickname for this dish",
      "ingredients": ["1 cup ingredient 1", "2 tbsp ingredient 2", "1 tsp spice"],
      "steps": [
        "Step 1: Prep & Chopping details...",
        "Step 2: Tempering & Heating instructions with flame level and minutes...",
        "Step 3: Sautéing and spice aroma checkpoints...",
        "Step 4: Main ingredient simmer & cover details...",
        "Step 5: Seasoning & texture testing...",
        "Step 6: Final garnish & resting time...",
        "Step 7: Serving recommendations..."
      ],
      "fun_fact": "A fascinating or hilarious fun fact about this dish",
      "youtube_query": "Exact YouTube search query for video tutorial",
      "prep_time": "25 mins",
      "difficulty": "Medium",
      "nutrition": {{
        "calories": "380 kcal",
        "protein": "18g",
        "carbs": "24g",
        "fat": "20g",
        "health_score": "8.8/10",
        "health_badge": "High Protein & Balanced"
      }}
    }}
  ]
}}
Make sure all text string values are in {language} language. Return ONLY valid JSON."""

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful culinary AI assistant providing 3 detailed step-by-step recipes in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} if hasattr(client.chat.completions, 'create') else None,
                temperature=0.7,
                max_tokens=2500,
            )
            raw_text = response.choices[0].message.content.strip()
            data = json.loads(raw_text)
            
            recipe_list = []
            raw_recipes = data.get("recipes", [])
            if isinstance(raw_recipes, list) and len(raw_recipes) > 0:
                for item in raw_recipes:
                    yt_q = item.get("youtube_query", f"{item.get('title', 'recipe')} tutorial")
                    vid_id = fetch_youtube_video_id(yt_q) or ""
                    recipe_list.append({
                        "title": item.get("title", "AI Fusion Delight"),
                        "funny_title": item.get("funny_title", "The Unexpected Flavor Explosion"),
                        "ingredients": item.get("ingredients", [i.strip() for i in ingredients_text.split(',')]),
                        "steps": item.get("steps", ["Prep ingredients", "Cook on medium flame", "Serve hot"]),
                        "fun_fact": item.get("fun_fact", "Cooking with love enhances taste by 100%!"),
                        "youtube_query": yt_q,
                        "youtube_video_id": vid_id,
                        "prep_time": item.get("prep_time", "20 mins"),
                        "difficulty": item.get("difficulty", "Medium"),
                        "nutrition": item.get("nutrition", {
                            "calories": "350 kcal", "protein": "16g", "carbs": "26g", "fat": "18g",
                            "health_score": "8.5/10", "health_badge": "Balanced & Healthy"
                        }),
                        "language": language
                    })
                return recipe_list
        except Exception as e:
            print(f"OpenAI Recipe Generation error: {e}")

    # Offline/Fallback generation (Returns 3 options)
    return _generate_fallback_recipes(ingredients_text, language)


def ask_voice_chef_ai(question, recipe_title="", ingredients="", current_step=""):
    """
    AI Voice Chef Assistant: Real-time cooking troubleshooting & ingredient substitutions.
    """
    client = get_openai_client()
    prompt = f"""You are FoodyFi AI Master Chef Assistant.
The user is currently cooking: {recipe_title or 'a dish'}.
Ingredients: {ingredients}
Current Step: {current_step}

User Question: "{question}"

Provide a concise, expert answer in 2 short sentences. If asking for a substitute, suggest 2 easy alternatives."""

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful expert chef assistant. Keep answers brief, encouraging, and clear."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=180,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Voice Chef OpenAI error: {e}")

    # Fallback smart culinary answers
    q_lower = question.lower()
    if "cream" in q_lower or "milk" in q_lower:
        return "You can substitute heavy cream with full-fat milk mixed with melted butter, or Greek yogurt/cashew cream for rich texture!"
    elif "spicy" in q_lower or "chili" in q_lower or "pepper" in q_lower:
        return "To tone down spiciness, stir in a dollop of yogurt, cream, butter, or half a teaspoon of sugar/lemon juice."
    elif "salt" in q_lower:
        return "If your dish is too salty, simmer with a raw peeled potato chunk or add a splash of milk/water to dilute the sodium!"
    elif "butter" in q_lower or "oil" in q_lower:
        return "You can use ghee, coconut oil, or olive oil as a healthy 1-to-1 substitute for butter."
    else:
        return f"Great cooking question! Keep your flame on medium, taste as you adjust spices, and simmer gently for best aroma."


def generate_food_image_ai(recipe_title):
    """
    Generates a food photo URL using OpenAI DALL-E or Pollinations AI image generator fallback.
    """
    client = get_openai_client()
    if client:
        try:
            image_prompt = f"Professional studio food photography of delicious {recipe_title}, gourmet presentation, warm lighting, 4k resolution, food magazine cover style"
            response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            print(f"DALL-E image generation error: {e}")

    # Pollinations AI fallback (Free, reliable AI image generator API)
    encoded_prompt = urllib.parse.quote(f"delicious cooked dish {recipe_title} food photography high quality")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true&seed={random.randint(1, 99999)}"


def _generate_fallback_recipes(ingredients_text, language):
    clean_ing = [i.strip() for i in ingredients_text.split(',') if i.strip()]
    main_item = clean_ing[0].capitalize() if clean_ing else "Special Ingredient"
    sec_item = clean_ing[1].capitalize() if len(clean_ing) > 1 else "Tomato"

    if language == 'Hindi':
        recipes_list = [
            {
                "title": f"शाही {main_item} मलाई करी",
                "funny_title": f"पेट पूजा का धमाकेदार {main_item} खजाना",
                "ingredients": clean_ing or ["250g मुख्य सामग्री", "2 बारीक कटे टमाटर", "1 चम्मच अदरक-लहसुन पेस्ट", "गरम मसाला"],
                "steps": [
                    f"चरण 1: {main_item} को मध्यम टुकड़ों में काटें और प्याज, टमाटर बारीक काट लें।",
                    "चरण 2: कढ़ाई में 2 चम्मच तेल या घी गर्म करें और जीरा चटकाएं।",
                    "चरण 3: अदरक-लहसुन पेस्ट और प्याज को सुनहरा होने तक भूनें।",
                    "चरण 4: टमाटर और मसाले डालकर तेल अलग होने तक पकाएं।",
                    f"चरण 5: {main_item} और आधा कप पानी मिलाकर 6 मिनट धीमी आंच पर पकाएं।",
                    "चरण 6: गरम मसाला और ताजा धनिया डालकर गरमा-गरम परोसें!"
                ],
                "fun_fact": "धीमी आंच पर पकाए गए मसाले भोजन में बेहतरीन सुगंध लाते हैं!",
                "youtube_query": f"{main_item} recipe in hindi video tutorial",
                "prep_time": "25 मिनट",
                "difficulty": "आसान",
                "language": "Hindi"
            },
            {
                "title": f"क्रिस्पी {main_item} और {sec_item} तवा फ्राई",
                "funny_title": f"चटपटा शाम का {main_item} स्नैक",
                "ingredients": clean_ing or ["मुख्य सामग्री", "बेसन/अरारोट", "लाल मिर्च", "चाट मसाला", "तेल"],
                "steps": [
                    f"चरण 1: {main_item} को पतली स्लाइस में काट लें।",
                    "चरण 2: कटोरी में बेसन, नमक, चाट मसाला और थोड़ा पानी डालकर गाढ़ा घोल बनाएं।",
                    "चरण 3: टुकड़ों को घोल में डिप करके तवे पर गर्म तेल में डालें।",
                    "चरण 4: दोनों तरफ से 4-5 मिनट तक क्रिस्पी सुनहरा होने तक शैलो फ्राई करें।",
                    "चरण 5: हरी चटनी और नींबू के साथ परोसें!"
                ],
                "fun_fact": "चाट मसाला डालने से तवा फ्राई का स्वाद 2 गुना बढ़ जाता है!",
                "youtube_query": f"crispy {main_item} fry recipe in hindi",
                "prep_time": "15 मिनट",
                "difficulty": "बहुत आसान",
                "language": "Hindi"
            },
            {
                "title": f"हेल्दी {main_item} मखमली सूप",
                "funny_title": f"दिल और दिमाग को ताज़गी देने वाला सूप",
                "ingredients": clean_ing or ["मुख्य सामग्री", "सब्जियां", "काली मिर्च", "बखन/ऑलिव ऑयल"],
                "steps": [
                    f"चरण 1: {main_item} और सब्जियों को धोकर उबाल लें।",
                    "चरण 2: उबली सब्जियों को मिक्सी में पीसकर स्मूथ प्यूरी बना लें।",
                    "चरण 3: पैन में थोड़ा मक्खन गर्म करके प्यूरी और काली मिर्च पाउडर मिलाएं।",
                    "चरण 4: 5 मिनट तक उबालें और ब्रेड क्रूटॉन्स के साथ सर्व करें!"
                ],
                "fun_fact": "गरम सूप शरीर की इम्युनिटी बढ़ाने में मदद करता है!",
                "youtube_query": f"healthy {main_item} soup recipe in hindi",
                "prep_time": "20 मिनट",
                "difficulty": "मध्यम",
                "language": "Hindi"
            }
        ]
    elif language == 'Kannada':
        recipes_list = [
            {
                "title": f"ರಾಜಕೀಯ {main_item} ಮಸಾಲೆ ರಸದೂಟ",
                "funny_title": f"ಹೊಟ್ಟೆಗೆ ಸಖತ್ ತಂಪಾದ {main_item} ಧಮಾಕಾ",
                "ingredients": clean_ing or ["250 ಗ್ರಾಂ ಮುಖ್ಯ ಪದಾರ್ಥ", "2 ಟೊಮೆಟೊ", "ಶುಂಠಿ ಬೆಳ್ಳುಳ್ಳಿ ಪೇಸ್ಟ್", "ಸಾಂಬಾರ್ ಪುಡಿ"],
                "steps": [
                    f"ಹಂತ 1: {main_item} ಹಾಗೂ ಈರುಳ್ಳಿ, ಟೊಮೆಟೊ ಸಣ್ಣಗೆ ಹೆಚ್ಚಿಟ್ಟುಕೊಳ್ಳಿ.",
                    "ಹಂತ 2: ಬಾಣಲೆಯಲ್ಲಿ 2 ಚಮಚ ಎಣ್ಣೆ ಕಾಯಿಸಿ ಸಾಸಿವೆ, ಜೀರಿಗೆ ಒಗ್ಗರಣೆ ಹಾಕಿ.",
                    "ಹಂತ 3: ಈರುಳ್ಳಿ ಮತ್ತು ಶುಂಠಿ-ಬೆಳ್ಳುಳ್ಳಿ ಪೇಸ್ಟ್ ಚೆನ್ನಾಗಿ ಹುರಿಯಿರಿ.",
                    "ಹಂತ 4: ಟೊಮೆಟೊ ಹಾಗೂ ಮಸಾಲೆ ಪುಡಿ ಸೇರಿಸಿ ಎಣ್ಣೆ ತೇಲುವವರೆಗೆ ಬೇಯಿಸಿ.",
                    f"ಹಂತ 5: {main_item} ತುಂಡುಗಳು ಮತ್ತು ನೀರು ಸೇರಿಸಿ 6 ನಿಮಿಷ ಸಣ್ಣ ಉರಿಯಲ್ಲಿ ಕುದಿಸಿ.",
                    "ಹಂತ 6: ಕೊತ್ತಂಬರಿ ಸೊಪ್ಪು ಉದುರಿಸಿ ಬಿಸಿ ಬಿಸಿ ಅನ್ನದೊಂದಿಗೆ ಸವಿಯಿರಿ!"
                ],
                "fun_fact": "ಸಣ್ಣ ಉರಿಯಲ್ಲಿ ಬೆಂದ ಮಸಾಲೆ ಅಡುಗೆ ಆರೋಗ್ಯಕ್ಕೆ ಸಖತ್ ಒಳ್ಳೆಯದು!",
                "youtube_query": f"{main_item} recipe in kannada tutorial",
                "prep_time": "25 ನಿಮಿಷ",
                "difficulty": "ಸುಲಭ",
                "language": "Kannada"
            },
            {
                "title": f"ಕ್ರಿಸ್ಪಿ {main_item} ತವಾ ಫ್ರೈ",
                "funny_title": f"ಸಂಜೆ ಟೀ ಜೊತೆ ಸೂಪರ್ {main_item} ತಿಂಡಿ",
                "ingredients": clean_ing or ["ಮುಖ್ಯ ಪದಾರ್ಥ", "ಕಡಲೆ ಹಿಟ್ಟು", "ಖಾರದ ಪುಡಿ", "ಉಪ್ಪು", "ಎಣ್ಣೆ"],
                "steps": [
                    f"ಹಂತ 1: {main_item} ಸಣ್ಣಗೆ ಹೆಚ್ಚಿಟ್ಟುಕೊಳ್ಳಿ.",
                    "ಹಂತ 2: ಹಿಟ್ಟಿಗೆ ಖಾರದ ಪುಡಿ ಮತ್ತು ಉಪ್ಪು ಹಾಕಿ ಕಲಸಿಕೊಳ್ಳಿ.",
                    "ಹಂತ 3: ಎಣ್ಣೆಯಲ್ಲಿ ಕ್ರಿಸ್ಪಿಯಾಗಿ 4-5 ನಿಮಿಷ ಕರಿಯಿರಿ.",
                    "ಹಂತ 4: ಬಿಸಿ ಬಿಸಿಯಾಗಿ ಚಟ್ನಿ ಜೊತೆ ಸವಿಯಿರಿ!"
                ],
                "fun_fact": "ಕ್ರಿಸ್ಪಿ ಫ್ರೈಗೆ ನಿಂಬೆ ರಸ ಹಿಂಡಿದರೆ ರುಚಿ ಹೆಚ್ಚುತ್ತದೆ!",
                "youtube_query": f"crispy {main_item} fry recipe in kannada",
                "prep_time": "15 ನಿಮಿಷ",
                "difficulty": "ಬಹಳ ಸುಲಭ",
                "language": "Kannada"
            },
            {
                "title": f"ಆರೋಗ್ಯಕರ {main_item} ರಸಂ ಸূপ್",
                "funny_title": f"ದೇಹಕ್ಕೆ ಶಕ್ತಿ ಕೊಡುವ ಫ್ರೆಶ್ ಸೂಪ್",
                "ingredients": clean_ing or ["ಮುಖ್ಯ ಪದಾರ್ಥ", "ಕಾಳುಮೆಣಸು", "ಜೀರಿಗೆ", "ಕೊತ್ತಂಬರಿ"],
                "steps": [
                    f"ಹಂತ 1: {main_item} ಬೇಯಿಸಿ ಮಸೆಯಿರಿ.",
                    "ಹಂತ 2: ಜೀರಿಗೆ ಕಾಳುಮೆಣಸಿನ ಒಗ್ಗರಣೆ ಕೊಡಿ.",
                    "ಹಂತ 3: 5 ನಿಮಿಷ ಕುದಿಸಿ ಬಿಸಿಯಾಗಿ ಕುಡಿಯಿರಿ!"
                ],
                "fun_fact": "ಬಿಸಿ ಸೂಪ್ ಶೀತ ಮತ್ತು ಕೆಮ್ಮಿಗೆ ತಕ್ಷಣ ಶಮನ ನೀಡುತ್ತದೆ!",
                "youtube_query": f"healthy {main_item} soup recipe in kannada",
                "prep_time": "20 ನಿಮಿಷ",
                "difficulty": "ಮಧ್ಯಮ",
                "language": "Kannada"
            }
        ]
    else: # English
        recipes_list = [
            {
                "title": f"Gourmet Royal {main_item} Butter Masala",
                "funny_title": f"The Ultimate {main_item} Flavor Explosion",
                "ingredients": clean_ing or ["250g Paneer/Main Ingredient", "2 Tomatoes", "1 tbsp Ginger-Garlic Paste", "Garam Masala & Spices"],
                "steps": [
                    f"Step 1: Prep & Chopping — Cut the {main_item} into uniform bite-sized cubes. Dice onions and tomatoes finely.",
                    "Step 2: Tempering Aromatics — Heat 2 tbsp butter or oil in a pan over medium heat. Add cumin seeds and crackle.",
                    "Step 3: Sautéing Aromatics — Toss in onions and ginger-garlic paste. Sauté for 4 minutes until golden brown.",
                    "Step 4: Cooking Gravy — Add tomatoes, turmeric, chili powder, coriander powder, and salt. Cook until oil separates.",
                    f"Step 5: Simmering — Add {main_item} cubes with 1/2 cup warm water. Cover and simmer on low flame for 6 minutes.",
                    "Step 6: Serve — Sprinkle fresh cilantro and serve hot with naan or rice!"
                ],
                "fun_fact": f"Did you know? Cooking on low heat enhances aromatic essential oils, making {main_item} dishes 2x more flavorful!",
                "youtube_query": f"{main_item} butter masala recipe video tutorial",
                "prep_time": "25 mins",
                "difficulty": "Medium",
                "language": "English"
            },
            {
                "title": f"Crispy Garlic {main_item} & {sec_item} Stir-Fry",
                "funny_title": f"Quick 15-Minute {main_item} Crunch Feast",
                "ingredients": clean_ing or ["Main Ingredient", "Garlic cloves", "Soy Sauce / Spices", "Olive Oil", "Black Pepper"],
                "steps": [
                    f"Step 1: Slice {main_item} into thin strips and crush garlic cloves.",
                    "Step 2: Heat 1.5 tbsp olive oil in a skillet or wok over high flame.",
                    "Step 3: Toss in minced garlic and sizzle for 30 seconds until aromatic.",
                    f"Step 4: Add {main_item} strips and stir-fry rapidly on high heat for 5 minutes.",
                    "Step 5: Drizzle soy sauce, black pepper, and chili flakes. Serve sizzling hot!"
                ],
                "fun_fact": "High-heat stir frying locks in nutrients and gives a smoky restaurant-style aroma!",
                "youtube_query": f"crispy garlic {main_item} stir fry recipe video",
                "prep_time": "15 mins",
                "difficulty": "Easy",
                "language": "English"
            },
            {
                "title": f"Creamy Velvet {main_item} Comfort Soup",
                "funny_title": f"Warm Hug in a Bowl {main_item} Delicacy",
                "ingredients": clean_ing or ["Main Ingredient", "Vegetable Broth", "Butter", "Crushed Pepper", "Fresh Cream"],
                "steps": [
                    f"Step 1: Chop {main_item} into chunks and boil gently in 2 cups broth.",
                    "Step 2: Blend the simmered mix until smooth and velvety.",
                    "Step 3: Transfer back to pot, melt 1 tbsp butter and season with black pepper.",
                    "Step 4: Simmer for 4 minutes, swirl fresh cream on top, and serve with garlic bread!"
                ],
                "fun_fact": "Adding a dollop of butter at the end gives soups a silky French bistro texture!",
                "youtube_query": f"creamy {main_item} soup recipe tutorial",
                "prep_time": "20 mins",
                "difficulty": "Easy",
                "language": "English"
            }
        ]

    for item in recipes_list:
        item["youtube_video_id"] = fetch_youtube_video_id(item.get("youtube_query")) or ""

    return recipes_list


