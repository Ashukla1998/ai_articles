import streamlit as st
import moviepy as mp
from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("🎥 Video to Career Article Generator")

# Language selection
language = st.selectbox("Choose language for article output:", ["English", "Hindi"])

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

# Initialize session state variables
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "article_en" not in st.session_state:
    st.session_state.article_en = None
if "article_hi" not in st.session_state:
    st.session_state.article_hi = None
if "video_processed" not in st.session_state:
    st.session_state.video_processed = False
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

def process_video(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(file.read())
        video_path = temp_video.name

    st.success("✅ Video uploaded successfully!")

    # Extract and compress audio
    st.info("Extracting audio from video...")
    video = mp.VideoFileClip(video_path)
    audio = video.audio

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        audio_path = temp_audio.name
        audio.write_audiofile(audio_path, codec="mp3", bitrate="64k")

    st.success("✅ Audio extracted and compressed!")

    # Transcribe audio
    st.info("Transcribing audio (this may take some time)...")
    with open(audio_path, "rb") as af:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=af
        )

    transcript_text = transcription.text.strip()
    st.success("✅ Transcription complete!")

    if not transcript_text:
        st.error("❌ No transcript content found. Please upload a valid video.")
        return

    # Updated and strict prompt
    prompt = f"""
        You are an expert career guide. Based ONLY on the following transcript, create a detailed and structured career article in the exact format below:

        1. **Brief Introduction of the Speaker** (if available)
        2. **What is it?**  
        - Definition (only if provided by the speaker; otherwise use a general defination of that role)  
        - Overview of the role or career path

        3. **Education**  
        - According to the speaker: List any qualifications, courses, or educational background mentioned in the transcript  
        - Other required qualifications (if not take help from internet but link the source): Include degrees, certifications, or training requirements

        4. **Skills**  
        - According to the speaker: List skills or abilities the speaker mentioned  
        - Other necessary skills (if not take help from internet but link the source): Include additional skills required for this career

        5. **Positives**  
        - According to the speaker:include benefits or rewarding aspects as described by the speaker
        - other positives (if not take help from internet but link the source): Include additional advantages of this career

        6. **Challenges**  
        - According to the speaker: include difficulties or drawbacks mentioned by the speaker
        - other challenges (if not take help from internet but link the source): Include additional challenges faced in this career

        7. **A Day in the Life**  
        - Describe a typical day based only on the speaker’s explanation

        ⚡ **Rules:**
        - Understand the transcript thoroughly before writing and add content in it.
        - If a section is not covered in the transcript, clearly write: **“Not mentioned in transcript.”**
        - Each section must be clearly labeled and strictly reflect content from the transcript.
        - Assign a **weightage (%)** to each section (except the introduction). The total must equal **100%**.  
        - Briefly explain how the weightage was calculated (based on the speaker’s emphasis or time spent discussing the topic).
        - Use **clear headings** and **bullet points** for easy readability.
        - You may use **realistic placeholder quotes** (e.g., “As I experienced in my role…”) only **if supported** by the transcript.
        - Use **simple, clear language**.
        - Write from the speaker’s perspective using **“I”** or **“we”** where appropriate.

        Transcript:
        \"\"\"{transcript_text}\"\"\"

        """

    st.info("Generating structured article from transcript...")
    article_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that formats transcripts into structured career articles."},
            {"role": "user", "content": prompt}
        ]
    )

    article_text = article_response.choices[0].message.content.strip()
    st.success("✅ Article generated in English!")

    # Store in session
    st.session_state.transcript = transcript_text
    st.session_state.article_en = article_text
    st.session_state.article_hi = None  # Reset Hindi translation
    st.session_state.video_processed = True

# Run only if new file uploaded
if uploaded_file is not None:
    if not st.session_state.video_processed or uploaded_file != st.session_state.last_uploaded_file:
        process_video(uploaded_file)
        st.session_state.last_uploaded_file = uploaded_file

# Display result
if st.session_state.video_processed:
    if language == "English":
        article_text = st.session_state.article_en
    else:
        # Translate if not cached
        if st.session_state.article_hi is None:
            st.info("Translating article to Hindi...")
            translation_prompt = f"""
Translate the following article to Hindi. Preserve all formatting (headings, bullet points, weightage etc.):

\"\"\"{st.session_state.article_en}\"\"\"
"""
            translation_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a translator that converts English content to Hindi, preserving formatting."},
                    {"role": "user", "content": translation_prompt}
                ]
            )
            st.session_state.article_hi = translation_response.choices[0].message.content.strip()
            st.success("✅ Article translated to Hindi!")

        article_text = st.session_state.article_hi

    # Display article
    st.subheader("📄 Generated Article")
    st.markdown(article_text)

    # Download buttons
    st.download_button(
        label="⬇️ Download Article as TXT",
        data=article_text,
        file_name="article.txt",
        mime="text/plain"
    )

    st.download_button(
        label="⬇️ Download Transcript as TXT",
        data=st.session_state.transcript,
        file_name="transcript.txt",
        mime="text/plain"
    )
