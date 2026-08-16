# 🍲 FoodyFi – AI Smart Cooking Assistant

FoodyFi is an AI-powered smart cooking assistant web application that helps users generate recipes, detect ingredients from images, and cook hands-free using a multilingual voice assistant.

Built with **Django**, **MongoDB Atlas**, **OpenAI APIs**, and a modern **Glassmorphism UI**, FoodyFi brings AI into your kitchen experience.

---

## 🚀 Features

### 🤖 AI Recipe Generation

* Generate recipes in:

  * English 🇺🇸
  * Kannada ಕನ್ನಡ
  * Hindi हिंदी
* Detailed **6–8 step instructions**
* Includes:

  * Flame levels 🔥
  * Cooking time ⏱️
  * Spice ratios 🌶️
  * Garnishing tips 🍽️

---

### 📸 AI Vision Ingredient Detection

* Upload an image → Detect ingredients using AI Vision

---

### 🔐 MongoDB Authentication

* Secure login & registration
* Password hashing (PBKDF2)
* Session-based login system

---

### 🎤 Multilingual Voice Assistant

* Hands-free cooking mode
* Commands in English, Kannada, Hindi

---

### 🎨 Modern UI

* Glassmorphism design
* Responsive interface

---

## 🛠️ Tech Stack

| Layer       | Technology                        |
| ----------- | --------------------------------- |
| Backend     | Django (Python)                   |
| Database    | MongoDB Atlas                     |
| AI Services | OpenAI GPT-4o, Vision API, DALL·E |
| Frontend    | HTML, CSS, JavaScript             |
| Voice       | Web Speech API                    |

---

# ⚙️ How to Run the Project (Step-by-Step)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/foodyfi.git
cd foodyfi
```

---

### 2️⃣ Install Python Packages

```bash
pip install django pymongo dnspython certifi openai python-dotenv
```

---

### 3️⃣ Create `.env` File

In the root folder, create a `.env` file and add:

```
MONGODB_URI=your_mongodb_atlas_uri
OPENAI_API_KEY=your_openai_api_key
```

⚠️ Never share your real credentials publicly.

---

### 4️⃣ Setup MongoDB Atlas

* Create a cluster in MongoDB Atlas
* Add your IP in **Network Access**
* Create database: `foodyfi_db`
* Collection: `users`

---

### 5️⃣ Run Migrations (Optional)

```bash
python manage.py migrate
```

---

### 6️⃣ Start the Server

```bash
python manage.py runserver
```

---

### 7️⃣ Open in Browser

Go to:

```
http://127.0.0.1:8000/
```

---

### 8️⃣ Usage Flow

1. Register → `/register/`
2. Login → `/login/`
3. Start generating recipes 🍲

---

## 🗄️ Database Schema

```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "hashed_password",
  "full_name": "User Name",
  "bio": "Food preferences",
  "favorite_cuisine": "All",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

---

## 🎤 Voice Commands

| Action | English | Hindi | Kannada  |
| ------ | ------- | ----- | -------- |
| Next   | next    | आगे   | ಮುಂದೆ    |
| Back   | back    | पीछे  | ಹಿಂದೆ    |
| Listen | listen  | सुनो  | ಕೇಳು     |
| Stop   | stop    | रुको  | ನಿಲ್ಲಿಸು |

---

## 📁 Project Structure

```
foodyfi/
├── manage.py
├── .env
├── foodyfi/
└── recipes/
```

---

## ⚠️ Security Notes

* Use `.env` for secrets
* Do NOT upload credentials to GitHub
* Enable MongoDB IP whitelist

---

## 📌 Future Improvements

* Mobile App (Flutter)
* Smart grocery list
* Nutrition analysis

---

## 👨‍💻 Author

**Raju Hakki**

---

## ⭐ Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it

---

**FoodyFi – Smart Cooking with AI 🍳🤖**
