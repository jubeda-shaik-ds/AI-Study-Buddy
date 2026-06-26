import streamlit as st
st.set_page_config(page_title="AI Study Buddy PRO", layout="wide")

import google.generativeai as genai
from PIL import Image
import PyPDF2
from docx import Document
import speech_recognition as sr
import json, os, time
import re

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------- API ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- FILES ----------------
CHAT_FILE = "chat_history.json"
PREF_FILE = "user_pref.json"

# ---------------- LOAD/SAVE ----------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# ---------------- SIDEBAR SETTINGS ----------------
st.sidebar.title("⚙️ Settings")

prefs = load_json(PREF_FILE)

language = st.sidebar.selectbox(
    "🌍 Language",
    ["English", "Telugu", "Hindi"],
    index=["English","Telugu","Hindi"].index(prefs.get("lang","English"))
)

difficulty = st.sidebar.selectbox(
    "🎯 Difficulty",
    ["easy","medium","hard"],
    index=["easy","medium","hard"].index(prefs.get("level","medium"))
)

save_json(PREF_FILE, {"lang": language, "level": difficulty})

mode = st.sidebar.selectbox(
    "Choose Mode",
    [
        "💬 Chat",
        "🧠 Study Tools",
        "📂 File Assistant",
        "🖼️ Image Chat",
        "📷 Camera",
        "🌐 Translate",
    
    ]
)

# ---------------- AI FUNCTION ----------------
def ai(prompt):
    try:
        final_prompt = f"""
IMPORTANT RULES:

1. If user explicitly asks a language (Tamil, Hindi, Telugu, etc),
   respond ONLY in that language.

2. Otherwise respond in {language}.

3. Keep explanation at {difficulty} level.

4. Correct spelling mistakes in user input before answering.

5. DO NOT mix languages.

6. If response requires STRICT FORMAT (like JSON, MCQ, code),
   DO NOT modify format.

Now respond:

{prompt}
"""
        final_prompt = final_prompt[:3000]

        response = model.generate_content(final_prompt)

        # ✅ SAFE CHECK
        if not response or not hasattr(response, "text") or not response.text:
            return "API_ERROR"

        return response.text

    except Exception as e:
        return f"API_ERROR: {str(e)}"

# ---------------- FILE READERS ----------------
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages[:5]:
        text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def image_ai(file):
    img = Image.open(file)
    response = model.generate_content(["Explain this image", img])
    return response.text if hasattr(response, "text") else str(response)

# ---------------- PDF EXPORT ----------------
import time

def create_pdf(text):

    file_name = f"notes_{int(time.time())}.pdf"

    # Detect language
    if any('\u0900' <= c <= '\u097F' for c in text):
        font_name = "Hindi"
        font_file = "NotoSansDevanagari-Regular.ttf"

    elif any('\u0C00' <= c <= '\u0C7F' for c in text):
        font_name = "Telugu"
        font_file = "NotoSansTelugu-Regular.ttf"

    else:
        font_name = "English"
        font_file = "NotoSans-Regular.ttf"

    # ✅ FIX: avoid font re-register error
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, font_file))

    doc = SimpleDocTemplate(file_name)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = font_name

    content = []

    for line in text.split("\n"):
        if line.strip():
            line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            content.append(Paragraph(line, style))

    doc.build(content)

    return file_name
# ---------------- CHAT SYSTEM ----------------
def load_history():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(data):
    with open(CHAT_FILE, "w") as f:
        json.dump(data, f)

if "current_chat" not in st.session_state:
    st.session_state.current_chat = []

if "chat_title" not in st.session_state:
    st.session_state.chat_title = "New Chat"

history = load_history()

# ---------------- UI ----------------
st.title("🤖 AI Study Buddy PRO")
st.caption("Smart Learning • AI Powered")

# ---------------- SIDEBAR CHAT ----------------
st.sidebar.subheader("💬 Chats")

search = st.sidebar.text_input("🔍 Search")

if st.sidebar.button("➕ New Chat"):
    st.session_state.current_chat = []
    st.session_state.chat_title = "New Chat"
    st.rerun()

if st.sidebar.button("💾 Save Chat"):
    if st.session_state.current_chat:
        history.append({
            "title": st.session_state.chat_title,
            "messages": st.session_state.current_chat
        })
        save_history(history)
        st.success("Saved!")

for i, chat in enumerate(history):
    title = chat["title"]

    if search and search.lower() not in title.lower():
        continue

    col1, col2, col3 = st.sidebar.columns([5,1,1])

    if col1.button(title, key=f"load_{i}"):
        st.session_state.current_chat = chat["messages"]
        st.session_state.chat_title = title
        st.rerun()

    if col2.button("✏", key=f"rename_{i}"):
        new_name = st.sidebar.text_input("Rename", key=f"name_{i}")
        if new_name:
            history[i]["title"] = new_name
            save_history(history)
            st.rerun()

    if col3.button("🗑", key=f"del_{i}"):
        history.pop(i)
        save_history(history)
        st.rerun()

# ---------------- CHAT MODE ----------------
if mode == "💬 Chat":

    st.subheader(f"🧠 {st.session_state.chat_title}")

    for msg in st.session_state.current_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user = st.chat_input("Ask anything...")

    if user:
        if len(st.session_state.current_chat) == 0:
            st.session_state.chat_title = user[:30]

        st.session_state.current_chat.append({"role":"user","content":user})

        with st.chat_message("user"):
            st.markdown(user)

        context = "\n".join(
            [f"{m['role']}: {m['content']}" for m in st.session_state.current_chat]
        )

        reply = ai(context)

        st.session_state.current_chat.append({"role":"assistant","content":reply})

        with st.chat_message("assistant"):
            st.markdown(reply)

# ---------------- STUDY ----------------
elif mode == "🧠 Study Tools":
    
    import time, json, re, os

    tool = st.selectbox(
        "Select Tool",
        ["Explain", "Summarize", "Quiz", "Flashcards"]
    )

    text = st.text_area("Enter topic/text")

    # ---------------- SESSION INIT ----------------
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "start_time" not in st.session_state:
        st.session_state.start_time = 0
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = []

    QUIZ_TIME = 15

    # ---------------- LANGUAGE DETECT ----------------
    def detect_output_language(text):
        if any('\u0C00' <= c <= '\u0C7F' for c in text):
            return "Telugu"
        elif any('\u0900' <= c <= '\u097F' for c in text):
            return "Hindi"
        else:
            return "English"

    # =========================================================
    # 🧠 EXPLAIN / SUMMARIZE / FLASHCARDS
    # =========================================================
    if tool in ["Explain", "Summarize", "Flashcards"]:

        if st.button(f"Generate {tool}"):

            if text.strip() == "":
                st.warning("⚠️ Enter topic/text")
            else:

                prompt = f"""
Tool: {tool}
Topic: {text}

Language: {language}
Difficulty: {difficulty}
"""

                with st.spinner("Generating..."):
                    result = ai(prompt)

                st.write(result)

                # -------- PDF LOGIC --------
                output_lang = detect_output_language(result)

                if output_lang in ["English", "Hindi", "Telugu"]:

                    pdf = create_pdf(result)

                    with open(pdf, "rb") as f:
                        st.download_button(
                            f"📥 Download {tool} PDF",
                            f,
                            file_name=f"{tool.lower()}.pdf"
                        )

                    os.remove(pdf)

                else:
                    st.info("📌 PDF only available in English, Hindi, Telugu")

                    if st.button("📥 Download in English"):

                        eng = ai(f"Translate into English:\n{result}")

                        pdf = create_pdf(eng)

                        with open(pdf, "rb") as f:
                            st.download_button(
                                "⬇ Download English PDF",
                                f,
                                file_name=f"{tool.lower()}_english.pdf"
                            )

                        os.remove(pdf)

    # =========================================================
    # 🧠 QUIZ (FIXED)
    # =========================================================
    elif tool == "Quiz":

        if not st.session_state.quiz_started:

            st.subheader("🧠 Quiz Mode")

            if st.button("🚀 Start Quiz"):

                if text.strip() == "":
                    st.warning("⚠️ Enter topic")
                else:

                    prompt = f"""
Generate 5 MCQs on: {text}

Language: {language}
Difficulty: {difficulty}

Return ONLY JSON:
[
{{"question":"","options":["A)","B)","C)","D)"],"answer":"A","explanation":""}}
]
"""

                    with st.spinner("Generating quiz..."):
                        result = ai(prompt)

                    if result == "API_ERROR":
                        st.error("⚠️ API limit reached")
                        st.stop()

                    cleaned = result.replace("```json", "").replace("```", "").strip()
                    match = re.search(r"\[.*\]", cleaned, re.DOTALL)

                    if not match:
                        st.error("⚠️ Invalid quiz format")
                        st.write(result)
                        st.stop()

                    json_str = match.group()

                    try:
                        data = json.loads(json_str)

                    except:
                        st.error("⚠️ Retry...")

                        result = ai(prompt)

                        cleaned = result.replace("```json", "").replace("```", "").strip()
                        match = re.search(r"\[.*\]", cleaned, re.DOTALL)

                        if match:
                            data = json.loads(match.group())
                        else:
                            st.error("⚠️ Failed again")
                            st.write(result)
                            st.stop()

                    # SAVE QUIZ
                    st.session_state.quiz_data = data
                    st.session_state.quiz_index = 0
                    st.session_state.score = 0
                    st.session_state.quiz_started = True
                    st.session_state.start_time = time.time()
                    st.session_state.user_answers = []

                    st.rerun()

        else:

            q = st.session_state.quiz_data[st.session_state.quiz_index]

            total = len(st.session_state.quiz_data)
            current = st.session_state.quiz_index + 1

            st.subheader(f"Q{current}: {q['question']}")
            st.progress(current / total)
            st.caption(f"Question {current} of {total}")

            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, QUIZ_TIME - int(elapsed))

            st.warning(f"⏳ Time left: {remaining} sec")

            selected = st.radio(
                "Choose answer:",
                q["options"],
                key=f"quiz_{current}"
            )

            # TIMEOUT
            if remaining == 0:

                st.session_state.user_answers.append({
                    "question": q["question"],
                    "selected": "Not Answered",
                    "correct": q["answer"],
                    "explanation": q["explanation"]
                })

                if current < total:
                    st.session_state.quiz_index += 1
                    st.session_state.start_time = time.time()
                    st.rerun()
                else:
                    st.session_state.quiz_started = False
                    st.rerun()

            # SUBMIT
            if st.button("✅ Submit Answer"):

                st.session_state.user_answers.append({
                    "question": q["question"],
                    "selected": selected,
                    "correct": q["answer"],
                    "explanation": q["explanation"]
                })

                if selected.startswith(q["answer"]):
                    st.session_state.score += 1

                if current < total:
                    st.session_state.quiz_index += 1
                    st.session_state.start_time = time.time()
                    st.rerun()
                else:
                    st.session_state.quiz_started = False
                    st.rerun()

            if remaining > 0:
                time.sleep(1)
                st.rerun()

    # =========================================================
    # 🧠 FINAL RESULT
    # =========================================================
    if (not st.session_state.quiz_started) and st.session_state.user_answers:

        st.success(f"🎉 Score: {st.session_state.score}/{len(st.session_state.user_answers)}")

        for i, ans in enumerate(st.session_state.user_answers):

            st.markdown(f"### Q{i+1}: {ans['question']}")

            if ans["selected"] == "Not Answered":
                st.warning("⏰ Not Answered")
                st.info(f"✔ {ans['correct']}")

            elif ans["selected"].startswith(ans["correct"]):
                st.success(f"✅ {ans['selected']}")

            else:
                st.error(f"❌ {ans['selected']}")
                st.info(f"✔ {ans['correct']}")

            st.write(f"💡 {ans['explanation']}")
    
# ---------------- FILE ASSISTANT ----------------
elif mode == "📂 File Assistant":
    
    import os

    files = st.file_uploader("Upload files", accept_multiple_files=True)

    tool = st.selectbox("Action", ["Explain", "Summarize"])

    if files:

        combined = ""

        for f in files:
            if f.name.endswith(".pdf"):
                combined += read_pdf(f)

            elif f.name.endswith(".docx"):
                combined += read_docx(f)

            elif f.type.startswith("image"):
                combined += image_ai(f)

        if st.button("Generate"):

            # ✅ USE GLOBAL LANGUAGE + DIFFICULTY
            if tool == "Explain":
                prompt = f"Explain this content in {language} at {difficulty} level:\n{combined}"
            else:
                prompt = f"Summarize this content in {language} at {difficulty} level:\n{combined}"

            result = ai(prompt)

            st.markdown("### 📌 Output")
            st.write(result)

            # =====================================================
            # 🔥 PDF DOWNLOAD (WITH ENGLISH FALLBACK LOGIC)
            # =====================================================

            # ✅ If global language is allowed → direct PDF
            if language in ["English", "Hindi", "Telugu"]:

                pdf = create_pdf(result)

                with open(pdf, "rb") as f:
                    st.download_button(
                        "📥 Download PDF",
                        f,
                        file_name=pdf
                    )

                os.remove(pdf)

            else:
                # ❗ If user asked another language manually (rare case)
                st.info("📥 Download available in English")

                english_result = ai(f"Translate this into English:\n{result}")

                pdf = create_pdf(english_result)

                with open(pdf, "rb") as f:
                    st.download_button(
                        "📥 Download PDF (English)",
                        f,
                        file_name=pdf
                    )

                os.remove(pdf)
elif mode == "🖼️ Image Chat":
    
    import os

    st.subheader("🖼️ AI Image Study Tutor")

    # ================= SESSION INIT =================
    if "image_session" not in st.session_state:
        st.session_state.image_session = []

    if "final_summary" not in st.session_state:
        st.session_state.final_summary = ""

    if "session_done" not in st.session_state:
        st.session_state.session_done = False

    # ================= IMAGE MODE =================
    image_mode = st.radio(
        "How many images?",
        ["Single Image", "Two Images"]
    )

    # ================= SINGLE IMAGE =================
    if image_mode == "Single Image":

        img = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

        if img:
            st.image(img)

            task = st.selectbox("Action", ["Explain", "Summarize"])

            if st.button("Analyze"):

                image = Image.open(img)

                prompt = f"{task} this image in {language} at {difficulty} level."

                result = model.generate_content([prompt, image]).text

                st.session_state.image_session = []
                st.session_state.image_session.append(result)

                st.write(result)

    # ================= TWO IMAGE =================
    else:

        img1 = st.file_uploader("Image 1", type=["jpg", "png", "jpeg"], key="i1")
        img2 = st.file_uploader("Image 2", type=["jpg", "png", "jpeg"], key="i2")

        if img1 and img2:

            col1, col2 = st.columns(2)
            with col1:
                st.image(img1)
            with col2:
                st.image(img2)

            if st.button("Compare"):

                prompt = f"""
Compare both images in {language} at {difficulty} level.
Explain similarities and differences clearly.
"""

                result = model.generate_content(
                    [prompt, Image.open(img1), Image.open(img2)]
                ).text

                st.session_state.image_session = []
                st.session_state.image_session.append(result)

                st.write(result)

    # ================= FOLLOW-UP (SPELL FIX) =================
    st.markdown("## 💬 Ask Question")

    follow_up = st.text_input("Ask here")

    if follow_up:

        # 🔥 SPELL FIX AUTOMATIC
        corrected = ai(f"Correct this sentence:\n{follow_up}")

        chat_prompt = f"""
Context:
{st.session_state.image_session}

User question:
{corrected}

Answer clearly.
"""

        reply = model.generate_content(chat_prompt).text

        st.write(reply)

        st.session_state.image_session.append(f"Q: {corrected}")
        st.session_state.image_session.append(f"A: {reply}")

    # ================= FINISH =================
    if st.button("Finish Session"):

        st.session_state.session_done = True

        final_summary = ai(f"""
Summarize clearly:

{st.session_state.image_session}

Give:
- Final summary
- Key points
""")

        # ✅ STORE ONLY FINAL
        st.session_state.final_summary = final_summary

        st.write(final_summary)

    # ================= DOWNLOAD (ONLY FINAL) =================
    if st.session_state.session_done:

        if st.button("📥 Download PDF"):

            pdf = create_pdf(st.session_state.final_summary)

            with open(pdf, "rb") as f:
                st.download_button("⬇ Download", f, file_name="final_notes.pdf")

            os.remove(pdf)

        if st.button("🔄 Reset"):
            st.session_state.image_session = []
            st.session_state.final_summary = ""
            st.session_state.session_done = False

elif mode == "📷 Camera":
    
    import os

    st.subheader("📷 AI Camera Study")

    # ================= SESSION INIT =================
    if "camera_session" not in st.session_state:
        st.session_state.camera_session = []

    if "camera_final" not in st.session_state:
        st.session_state.camera_final = ""

    if "camera_done" not in st.session_state:
        st.session_state.camera_done = False

    cam = st.camera_input("Take photo")

    tool = st.selectbox("Action", ["Explain", "Summarize"])

    # ================= IMAGE PROCESS =================
    if cam:

        st.image(cam)

        if st.button("Generate"):

            prompt = f"{tool} this image in {language} at {difficulty} level"

            result = model.generate_content([prompt, Image.open(cam)]).text

            st.session_state.camera_session = []
            st.session_state.camera_session.append(result)

            st.write(result)

    # ================= FOLLOW-UP (SPELL FIX) =================
    st.markdown("## 💬 Ask Question")

    follow_up = st.text_input("Ask about this image")

    if follow_up:

        # 🔥 SPELL CORRECTION
        corrected = ai(f"Correct this sentence:\n{follow_up}")

        chat_prompt = f"""
Context:
{st.session_state.camera_session}

User question:
{corrected}

Answer clearly.
"""

        reply = ai(chat_prompt)

        st.write(reply)

        st.session_state.camera_session.append(f"Q: {corrected}")
        st.session_state.camera_session.append(f"A: {reply}")

    # ================= FINISH =================
    if st.button("Finish Session"):

        st.session_state.camera_done = True

        final_summary = ai(f"""
Summarize clearly:

{st.session_state.camera_session}

Give:
- Final summary
- Key points
""")

        # ✅ STORE ONLY FINAL
        st.session_state.camera_final = final_summary

        st.write(final_summary)

    # ================= DOWNLOAD ONLY FINAL =================
    if st.session_state.camera_done:

        if st.button("📥 Download PDF"):

            pdf = create_pdf(st.session_state.camera_final)

            with open(pdf, "rb") as f:
                st.download_button(
                    "⬇ Download Final Notes",
                    f,
                    file_name="camera_final.pdf"
                )

            os.remove(pdf)

        if st.button("🔄 Reset"):
            st.session_state.camera_session = []
            st.session_state.camera_final = ""
            st.session_state.camera_done = False
# ---------------- TRANSLATE ----------------
elif mode == "🌐 Translate":
    
    st.subheader("🌐 AI Translator")

    txt = st.text_area("Enter text to translate")

    target_lang = st.selectbox(
        "Translate to",
        [
            "English",
            "Hindi",
            "Telugu",
            "Tamil",
            "Kannada",
            "Malayalam",
            "Spanish",
            "French",
            "German",
            "Chinese",
            "Arabic"
        ]
    )

    if st.button("Translate"):

        if txt.strip() == "":
            st.warning("⚠️ Please enter some text")
        else:
            prompt = f"""
Translate the following text into {target_lang}.
Keep meaning accurate and natural.

Text:
{txt}
"""

            result = ai(prompt)

            st.write(result)

            # 🔥 COPY BUTTON STYLE
            st.code(result, language="text")

