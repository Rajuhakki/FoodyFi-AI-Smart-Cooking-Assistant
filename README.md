# 🍲 FoodyFi – AI Smart Cooking Assistant

🌐 **Live Vercel Deployment**: [https://foody-fi-ai-smart-cooking-assistant-beta.vercel.app/](https://foody-fi-ai-smart-cooking-assistant-nine.vercel.app/login/)

**FoodyFi** is a state-of-the-art AI-powered smart cooking assistant web application. It helps users generate personalized recipes, analyze nutritional macros, manage smart grocery lists, detect ingredients from photos, and cook hands-free with a multilingual voice assistant and real-time AI Voice Chef!

Built with **Django**, **MongoDB Atlas**, **OpenAI GPT-4o & Vision APIs**, **Web Audio/Speech APIs**, and a modern **Glassmorphism UI design system**.

---

## ✨ Key Features

### 🤖 1. Multi-Recipe Choice Selection
* Generates **3 distinct recipe options** (Option 1: Classic Main Course, Option 2: Quick Stir Fry/Snack, Option 3: Creamy Soup/Special Fusion) for every ingredient input.
* Choose your favorite dish option with 1 click!

### 🥗 2. AI Nutrition & Health Breakdown
* Calculates macros for every recipe: **Calories**, **Protein**, **Carbs**, and **Fats**.
* Assigns an **AI Health Score** (e.g. `8.8/10`) and a dietary **Health Badge** (e.g. `High Protein & Balanced`).

### 🛒 3. Interactive Smart Grocery Checklist & WhatsApp Export
* **Pantry Checklist**: Mark off ingredients you already have.
* **Hide Checked Items 👁️**: 1-click filter to view ONLY what you need to buy at the store.
* **Export to WhatsApp 📲**: Instant formatted WhatsApp message with `✅ [HAVE]` and `🛒 [BUY]` tags.
* **PDF / Print & Copy**: 1-click printable PDF generator & clipboard copy.

### ⏱️ 4. Step-by-Step Timers & Web Audio API Alerts
* Automatically parses cooking step durations (e.g., *"5 minutes"*, *"30 seconds"*).
* Interactive timer widget with **Start**, **Pause**, and **Reset** controls.
* Web Audio API synth chime alert when the step timer finishes (`00:00`).

### 📸 5. Shareable Instagram-Style Recipe Story Cards
* 9:16 vertical Instagram Story Card modal with dish photo, macro stats, fun fact, and print/download button for social media.

### 🗣️ 6. Real-Time AI Voice Chef Assistant ("Ask Voice Chef")
* Ask questions directly while cooking: *"What can I use instead of cream?"* or *"My curry is too spicy!"*.
* Uses AI to return concise culinary answers AND **speaks the answer aloud using Text-To-Speech**!

### 🥑 7. Dietary & Health Preference Filters
* Select health preferences before generating:
  * 🥬 **Vegetarian / Vegan**
  * 🏋️ **High Protein**
  * 🥑 **Keto / Low Carb**
  * 🌾 **Gluten Free**
  * 🩺 **Diabetic Friendly**

### ♻️ 8. Zero-Waste Leftover Optimizer Mode
* Enable **Zero-Waste Fridge Mode** to instruct AI to utilize 100% of your input ingredients to eliminate food waste!

### 📺 9. Suggested YouTube Video Tutorials
* Automatically matches each recipe with exact YouTube tutorial query links for video guidance in English, Kannada, or Hindi.

### 🎤 10. Multilingual Voice Assistant & Vision Detection
* Speech-to-Text ingredient input & Vision Camera recognition.
* Voice-controlled hands-free Cooking Mode in **English**, **Kannada (ಕನ್ನಡ)**, and **Hindi (हिंदी)**.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3, Django 5 |
| **Database** | MongoDB Atlas (User Auth) & SQLite (Recipes) |
| **AI Services** | OpenAI GPT-4o, GPT-4 Vision, DALL·E 3 |
| **Frontend** | HTML5, Glassmorphism CSS3, Vanilla JS |
| **Audio & Speech** | Web Speech API & Web Audio API Synth |

---

## ⚙️ How to Run the Project

### 1️⃣ Clone Repository
```bash
git clone https://github.com/Rajuhakki/FoodyFi-AI-Smart-Cooking-Assistant.git
cd FoodyFi-AI-Smart-Cooking-Assistant
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Setup Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

### 4️⃣ Run Database Migrations
```bash
python manage.py migrate
```

### 5️⃣ Launch Development Server
```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser!

---

## 🎤 Hands-Free Voice Commands

| Action | English | Hindi (हिंदी) | Kannada (ಕನ್ನಡ) |
| :--- | :--- | :--- | :--- |
| **Next Step** | "Next" / "Forward" | "आगे" / "अगला" | "ಮುಂದೆ" |
| **Previous Step** | "Back" / "Previous" | "पीछे" | "ಹಿಂದೆ" |
| **Listen Step** | "Listen" / "Speak" | "सुनो" / "पढ़ो" | "ಓದು" / "ಕೇಳು" |
| **Stop Speech** | "Stop" / "Pause" | "रुको" | "ನಿಲ್ಲಿಸು" |

---

## 📁 Project Structure

```
FoodyFi/
├── foodyfi/            # Django project settings & routing
├── recipes/            # Recipe generator application
│   ├── ai_services.py  # OpenAI GPT-4o, Vision & Voice Chef logic
│   ├── mongo.py        # MongoDB Atlas database user auth
│   ├── models.py       # Recipe, Ratings & Reviews models
│   ├── views.py        # Views & API endpoints
│   ├── templates/      # Glassmorphism HTML templates
│   └── static/css/     # Modern CSS design system
├── requirements.txt    # Production dependencies
├── manage.py
└── README.md
```

---

## 👨‍💻 Author

**Raju Hakki** — *Creator & Lead Developer*
GitHub: [@Rajuhakki](https://github.com/Rajuhakki)

---

⭐ **If you like FoodyFi, give it a star on GitHub!** 🍲✨
