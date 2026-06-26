# 🤖 AI Study Buddy PRO

AI Study Buddy PRO is an AI-powered learning assistant built using **Streamlit** and the **Google Gemini API**. It helps students learn more effectively through interactive AI features, study tools, quizzes, file analysis, image understanding, translation, and PDF export.

## ✨ Features

* 💬 AI Chat Assistant
* 🧠 Study Tools

  * Explain
  * Summarize
  * Flashcards
  * Timed Quiz
* 📂 File Assistant (PDF, DOCX, Images)
* 🖼️ Image Chat
* 📷 Camera-Based Learning
* 🌐 AI Translator
* 📄 PDF Export
* 🌍 Multiple Language Support (English, Hindi, Telugu)
* 🎯 Difficulty Levels (Easy, Medium, Hard)
* 💾 Chat History
* ⚙️ User Preferences

## 🛠️ Technologies Used

* Python
* Streamlit
* Google Gemini API
* Pillow
* PyPDF2
* python-docx
* SpeechRecognition
* ReportLab

## 📦 Installation

1. Clone the repository.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Add your Gemini API key using Streamlit Secrets:

```toml
GEMINI_API_KEY = "YOUR_API_KEY"
```

4. Run the application:

```bash
streamlit run app.py
```

## 📁 Project Structure

* `app.py` – Main Streamlit application
* `requirements.txt` – Python dependencies
* `NotoSans-Regular.ttf` – English font
* `NotoSansDevanagari-Regular.ttf` – Hindi font
* `NotoSansTelugu-Regular.ttf` – Telugu font
* `chat_history.json` – Chat history storage
* `user_pref.json` – User preference storage

## 👨‍💻 Author
SHAIK JUBEDA
Developed as an AI-powered educational application using Streamlit and the Google Gemini API.
