import os
import json
import base64
import random
import urllib.parse
from django.conf import settings

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


def generate_recipe_ai(ingredients_text, language='English'):
    """
    Generates a full recipe (Title, Funny Title, Ingredients, Steps, Fun Fact)
    using OpenAI GPT model in the specified language (English, Kannada, Hindi).
    Includes intelligent fallback.
    """
    client = get_openai_client()
    
    lang_prompt_map = {
        'Kannada': 'in Kannada language (written in Kannada script)',
        'Hindi': 'in Hindi language (written in Devanagari script)',
        'English': 'in English'
    }
    target_lang_str = lang_prompt_map.get(language, 'in English')

    prompt = f"""You are FoodyFi, a world-class AI Master Chef and culinary expert.
Based on these available ingredients: {ingredients_text}

Generate a comprehensive, highly detailed, professional recipe {target_lang_str}.

REQUIREMENTS FOR STEPS:
- Provide 6 to 8 highly detailed, step-by-step cooking instructions.
- Specify exact stove flame levels (low, medium, high), precise timings in minutes, spice ratios, aroma checkpoints, and prep technique for every single step.
- Make each step clear, instructive, and complete so anyone can cook it flawlessly.

Return your response strictly in raw JSON format with the following keys:
{{
  "title": "Recipe Title",
  "funny_title": "A funny, catchy, humorous nickname for this dish",
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
  "fun_fact": "A fascinating or hilarious fun fact about this dish or key ingredient"
}}
Make sure all string values in the JSON are in {language} language. Return ONLY valid JSON."""

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful culinary AI assistant providing extremely detailed, step-by-step recipes in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} if hasattr(client.chat.completions, 'create') else None,
                temperature=0.7,
                max_tokens=1500,
            )
            raw_text = response.choices[0].message.content.strip()
            data = json.loads(raw_text)
            return {
                "title": data.get("title", "AI Fusion Dish"),
                "funny_title": data.get("funny_title", "The Unexpected Culinary Masterpiece"),
                "ingredients": data.get("ingredients", [i.strip() for i in ingredients_text.split(',')]),
                "steps": data.get("steps", ["Mix ingredients", "Cook thoroughly", "Enjoy!"]),
                "fun_fact": data.get("fun_fact", "Cooking with love makes food 50% tastier!"),
                "language": language
            }
        except Exception as e:
            print(f"OpenAI Recipe Generation error: {e}")

    # Offline/Fallback generation
    return _generate_fallback_recipe(ingredients_text, language)


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


def _generate_fallback_recipe(ingredients_text, language):
    clean_ing = [i.strip() for i in ingredients_text.split(',') if i.strip()]
    main_item = clean_ing[0].capitalize() if clean_ing else "Vegetable"
    
    if language == 'Hindi':
        return {
            "title": f"शाही {main_item} स्पेशल मलाई मसाला",
            "funny_title": f"पेट पूजा का धमाकेदार {main_item} खजाना",
            "ingredients": clean_ing or ["पनीर 250 ग्राम", "2 बारीक कटे टमाटर", "1 चम्मच अदरक-लहसुन पेस्ट", "1 चम्मच जीरा और गरम मसाला", "2 चम्मच देसी घी या तेल", "स्वादानुसार नमक और ताज़ा धनिया"],
            "steps": [
                f"चरण 1: तैयारी और कटाई — सबसे पहले {main_item} को मध्यम आकार के चौकोर टुकड़ों में काट लें। साथ ही प्याज, टमाटर और हरी मिर्च को बारीक काट कर अलग रख लें।",
                "चरण 2: तड़का लगाना — एक भारी तले की कढ़ाई में 2 चम्मच तेल या देसी घी मध्यम आंच पर गर्म करें। इसमें 1 चम्मच जीरा और चुटकी भर हींग डालकर 30 सेकंड तक चटकने दें।",
                "चरण 3: मसाला भूनना — अब कटा हुआ प्याज और अदरक-लहसुन का पेस्ट मिलाएं। इसे मध्यम आंच पर 4 से 5 मिनट तक तब तक भूनें जब तक कि प्याज हल्का सुनहरा न हो जाए।",
                "चरण 4: ग्रेवी पकाना — टमाटर, 1/2 चम्मच हल्दी, 1 चम्मच लाल मिर्च पाउडर, 1 चम्मच धनिया पाउडर और नमक डालें। मसालों को तब तक पकाएं जब तक कि किनारों से तेल न छूटने लगे (लगभग 4-5 मिनट)।",
                f"चरण 5: {main_item} मिलाना — अब कटे हुए {main_item} के टुकड़े और 1/2 कप गुनगुना पानी डालें। हल्के हाथों से मिलाएं ताकि टुकड़े टूटें नहीं।",
                "चरण 6: धीमी आंच पर सिमराना — कढ़ाई को ढक दें और धीमी आंच पर 6 से 8 मिनट तक पकने दें ताकि सारे मसालों का स्वाद अच्छी तरह रच-बस जाए।",
                "चरण 7: सजावट और सर्विंग — गैस बंद करें, ऊपर से गरम मसाला और ताजा कटा हरा धनिया छिड़कें। 2 मिनट ढक कर रखें फिर गरमा-गरम रोटी या चावल के साथ परोसें!"
            ],
            "fun_fact": "क्या आप जानते हैं? धीमी आंच पर पके मसालों की खुशबू और स्वाद दोगुना हो जाता है!",
            "language": "Hindi"
        }
    elif language == 'Kannada':
        return {
            "title": f"ರಾಜಕೀಯ {main_item} ಮಸಾಲೆ ರಸದೂಟ",
            "funny_title": f"ಹೊಟ್ಟೆಗೆ ಸಖತ್ ತಂಪಾದ {main_item} ಖಾರ ಧಮಾಕಾ",
            "ingredients": clean_ing or ["ಪನ್ನೀರ್ 250 ಗ್ರಾಂ", "2 ಸಣ್ಣಗೆ ಹೆಚ್ಚಿದ ಟೊಮೆಟೊ", "1 ಸ್ಪೂನ್ ಶುಂಠಿ-ಬೆಳ್ಳುಳ್ಳಿ ಪೇಸ್ಟ್", "1 ಸ್ಪೂನ್ ಧನಿಯಾ ಮತ್ತು ಸಾಂಬಾರ್ ಪುಡಿ", "2 ಸ್ಪೂನ್ ತುಪ್ಪ ಅಥವಾ ಎಣ್ಣೆ", "ರುಚಿಗೆ ತಕ್ಕಷ್ಟು ಉಪ್ಪು ಮತ್ತು ಕೊತ್ತಂಬರಿ ಸೊಪ್ಪು"],
            "steps": [
                f"ಹಂತ 1: ತರಕಾರಿ ಸಿದ್ಧತೆ — ಮೊದಲಿಗೆ {main_item} ಹಾಗೂ ಈರುಳ್ಳಿ, ಟೊಮೆಟೊ ಮತ್ತು ಹಸಿಮೆಣಸಿನಕಾಯಿಯನ್ನು ಸಣ್ಣಗೆ ಹೆಚ್ಚಿ ಪ್ರತ್ಯೇಕವಾಗಿ ಇಟ್ಟುಕೊಳ್ಳಿ.",
                "ಹಂತ 2: ಒಗ್ಗರಣೆ ಹಾಕುವುದು — ಬಾಣಲೆಯಲ್ಲಿ 2 ಚಮಚ ಎಣ್ಣೆ ಅಥವಾ ತುಪ್ಪವನ್ನು ಮಧ್ಯಮ ಉರಿಯಲ್ಲಿ ಕಾಯಿಸಿ, ಸಾಸಿವೆ, ಜೀರಿಗೆ ಹಾಗೂ ಕರಿಬೇವು ಹಾಕಿ 30 ಸೆಕೆಂಡು ಹುರಿಯಿರಿ.",
                "ಹಂತ 3: ಈರುಳ್ಳಿ ಹುರಿಯುವುದು — ಹೆಚ್ಚಿದ ಈರುಳ್ಳಿ ಮತ್ತು ಶುಂಠಿ-ಬೆಳ್ಳುಳ್ಳಿ ಪೇಸ್ಟ್ ಸೇರಿಸಿ, ಈರುಳ್ಳಿ ಹೊಂಬಣ್ಣಕ್ಕೆ ತಿರುಗುವವರೆಗೆ 4-5 ನಿಮಿಷ ಚೆನ್ನಾಗಿ ಬಾಡಿಸಿ.",
                "ಹಂತ 4: ಮಸಾಲೆ ಸಿದ್ಧತೆ — ಈಗ ಟೊಮೆಟೊ, ಅರಿಶಿನ, ಖಾರದ ಪುಡಿ, ಧನಿಯಾ ಪುಡಿ ಹಾಗೂ ಉಪ್ಪು ಸೇರಿಸಿ, ಎಣ್ಣೆ ತೇಲುವವರೆಗೆ 4 ನಿಮಿಷ ಸಣ್ಣ ಉರಿಯಲ್ಲಿ ಬೇಯಿಸಿ.",
                f"ಹಂತ 5: {main_item} ಸೇರಿಸುವುದು — ಬೇಯಿಸಿದ ಮಸಾಲೆಗೆ ಹೆಚ್ಚಿದ {main_item} ತುಂಡುಗಳು ಮತ್ತು ಅರ್ಧ ಲೋಟ ಬಿಸಿ ನೀರು ಸೇರಿಸಿ ಮೆಲ್ಲಗೆ ಕಲಸಿ.",
                "ಹಂತ 6: ಸಣ್ಣ ಉರಿಯಲ್ಲಿ ಬೇಯಿಸುವುದು — ಪಾತ್ರೆಯನ್ನು ಮುಚ್ಚಿ 6 ರಿಂದ 8 ನಿಮಿಷಗಳ ಕಾಲ ಸಣ್ಣ ಉರಿಯಲ್ಲಿ ಮಸಾಲೆ ಚೆನ್ನಾಗಿ ಹಿಡಿಯುವಂತೆ ಕುದಿಸಿ.",
                "ಹಂತ 7: ಅಲಂಕಾರ ಮತ್ತು ಬಡಿಸುವುದು — ಕೊನೆಯಲ್ಲಿ ಗರಂ ಮಸಾಲೆ ಹಾಗೂ ಸಣ್ಣಗೆ ಹೆಚ್ಚಿದ ಕೊತ್ತಂಬರಿ ಸೊಪ್ಪು ಉದುರಿಸಿ, ಬಿಸಿ ಬಿಸಿ ಅನ್ನ ಅಥವಾ ರೊಟ್ಟಿಯೊಂದಿಗೆ ಸವಿಯಿರಿ!"
            ],
            "fun_fact": "ತಿಳಿದಿದೆಯೇ? ಸಣ್ಣ ಉರಿಯಲ್ಲಿ ಬೆಂದ ಆಹಾರದ ಸುವಾಸನೆ ಮತ್ತು ಪೋಷಕಾಂಶಗಳು ದೇಹಕ್ಕೆ ಬಹಳ ಹಿತಕಾರಿ!",
            "language": "Kannada"
        }
    else: # English
        return {
            "title": f"Gourmet Royal {main_item} Butter Masala",
            "funny_title": f"The Ultimate {main_item} Flavor Explosion",
            "ingredients": clean_ing or ["250g Paneer/Main Item", "2 Finely Chopped Tomatoes", "1 tbsp Ginger-Garlic Paste", "1 tsp Garam Masala & Cumin", "2 tbsp Butter or Olive Oil", "Salt to taste & Fresh Cilantro"],
            "steps": [
                f"Step 1: Prep & Chopping — Cut the {main_item} into uniform bite-sized cubes. Dice onions, tomatoes, and green chilies finely for smooth gravy texture.",
                "Step 2: Tempering Aromatics — Heat 2 tbsp butter or oil in a heavy-bottomed pan over medium heat. Add cumin seeds and a pinch of asafoetida. Let crackle for 30 seconds.",
                "Step 3: Sautéing Aromatics — Toss in chopped onions and ginger-garlic paste. Sauté on medium flame for 4 to 5 minutes until onions turn translucent golden brown.",
                "Step 4: Cooking Spice Gravy — Stir in chopped tomatoes, turmeric, red chili powder, coriander powder, and salt. Cook for 5 minutes until oil separates from the gravy sides.",
                f"Step 5: Simmering Main Item — Add {main_item} cubes along with 1/2 cup warm water. Gently fold so the cubes absorb the rich gravy without breaking.",
                "Step 6: Low Flame Infusion — Cover the pan with a lid and simmer on low flame for 6 to 8 minutes allowing full spice infusion.",
                "Step 7: Final Garnish & Service — Sprinkle fresh garam masala and chopped cilantro. Let rest covered for 2 minutes, then serve piping hot with naan or rice!"
            ],
            "fun_fact": f"Did you know? Cooking on low heat enhances aromatic essential oils, making {main_item} dishes 2x more flavorful!",
            "language": "English"
        }

