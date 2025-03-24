import os
import streamlit as st
import tempfile
import time
import json
import assemblyai as aai
from utils import transcribe_audio, save_transcript_to_file, get_transcript_data, analyze_transcript_with_gpt
from dotenv import load_dotenv
import database as db
import datetime
import pandas as pd
import uuid
import auth  # Import the auth module

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="EchoScript AI",
    page_icon="🎙️",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Check for API keys
assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not assemblyai_api_key:
    st.error("❌ Assembly AI API key not found. Please update the .env file with your API key.")
    st.stop()

# Custom CSS for styling
st.markdown("""
<style>
    /* Import Google Fonts - Roboto for better readability */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Montserrat:wght@500;600;700&display=swap');
    
    :root {
        /* Color variables - Light Theme */
        --background-light: #FFFFFF;
        --background-card: #F7F7F7;
        --background-secondary: #EFEFEF;
        --primary-color: #FFCC00; /* Yellow */
        --accent-color: #FF9500;
        --text-color: #222222; /* Dark text */
        --text-secondary: #666666; /* Medium gray text */
        --text-on-primary: #000000; /* Black text for use on yellow backgrounds */
        --text-on-dark: #FFFFFF; /* White text for use on any dark backgrounds */
        --border-color: #E0E0E0;
        --success-color: #4CAF50;
        --error-color: #F44336;
        --border-radius: 8px;
        --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        --box-shadow-hover: 0 4px 8px rgba(0, 0, 0, 0.15);
        
        /* Standardized font sizes - only 4 sizes */
        --font-size-large: 1.8rem;
        --font-size-medium: 1.4rem;
        --font-size-normal: 1.1rem;
        --font-size-small: 0.9rem;
    }

    /* ---- ENFORCING TEXT COLOR CONTRAST ---- */
    /* Ensure Streamlit components with dark backgrounds always have light text */
    
    /* Force light text on any dark backgrounds */
    [style*="background-color: black"],
    [style*="background-color: #000"],
    [style*="background-color: #000000"],
    [style*="background: black"],
    [style*="background: #000"],
    [style*="background: #000000"],
    [class*="dark-bg"],
    .dark-background {
        color: var(--text-on-dark) !important;
    }
    
    /* Main app background and text */
    .stApp {
        background-color: var(--background-light);
        color: var(--text-color);
        font-family: 'Roboto', sans-serif;
        font-size: var(--font-size-normal);
        line-height: 1.6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"] {
        background-color: var(--background-card) !important;
    }
    
    /* Additional sidebar fixes */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: var(--text-color) !important;
    }
    
    /* Headers styling */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif;
        color: var(--text-color) !important;
        font-weight: 700 !important;
        letter-spacing: -0.015em;
        margin-bottom: 0.5em !important;
    }
    
    h1 {
        font-size: var(--font-size-large) !important;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        font-size: var(--font-size-medium) !important;
        margin-top: 1.5rem !important;
        color: var(--text-color) !important;
    }
    
    h3 {
        font-size: var(--font-size-medium) !important;
        color: var(--text-color) !important;
    }
    
    h4 {
        font-size: var(--font-size-normal) !important;
        color: var(--text-color) !important;
    }
    
    p, li, span, label, div {
        font-size: var(--font-size-normal) !important;
        color: var(--text-color);
    }
    
    /* Logo area */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        padding: 1.8rem;
        background-color: var(--background-card);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        border-left: 4px solid var(--primary-color);
    }
    
    .logo-icon {
        font-size: 3.5rem;
        margin-right: 1.5rem;
        color: var(--primary-color);
    }
    
    .logo-text h1 {
        margin: 0;
        padding: 0;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-fill-color: transparent;
    }
    
    .logo-text p {
        margin: 0.3rem 0 0 0;
        padding: 0;
        font-size: 1.2rem !important;
        color: var(--text-color);
        font-weight: 400;
    }
    
    /* Upload button styling */
    .upload-btn {
        background-color: var(--primary-color);
        color: var(--text-on-primary);
        padding: 0.9rem 1.6rem;
        border-radius: var(--border-radius);
        text-align: center;
        cursor: pointer;
        font-weight: 600;
        transition: background-color 0.3s, transform 0.2s;
        display: inline-block;
        margin-top: 1rem;
        box-shadow: var(--box-shadow);
        border: none;
        font-size: var(--font-size-normal) !important;
    }
    
    .upload-btn:hover {
        background-color: #FFE55C;
        transform: translateY(-2px);
        box-shadow: var(--box-shadow-hover);
    }
    
    /* Progress bars */
    .stProgress .st-bo {
        background-color: var(--primary-color);
        height: 10px !important;
    }
    
    .stProgress .st-bp {
        background-color: var(--background-secondary);
        height: 10px !important;
    }
    
    /* Result area */
    .result-area {
        background-color: var(--background-card);
        padding: 1.8rem;
        border-radius: var(--border-radius);
        margin-top: 1.8rem;
        border-left: 4px solid var(--primary-color);
        box-shadow: var(--box-shadow);
    }
    
    /* Analysis section */
    .analysis-section {
        background-color: var(--background-card);
        padding: 1.8rem;
        border-radius: var(--border-radius);
        margin-top: 1.8rem;
        border-left: 4px solid var(--primary-color);
        box-shadow: var(--box-shadow);
        position: relative;
    }
    
    .analysis-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.2rem;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.8rem;
    }
    
    .analysis-title {
        font-weight: 700;
        font-size: var(--font-size-medium);
        color: var(--text-color);
        margin: 0;
    }
    
    /* Alert boxes */
    .info-box {
        background-color: var(--background-secondary);
        color: var(--text-color);
        padding: 1rem 1.2rem;
        border-radius: var(--border-radius);
        margin-top: 1rem;
        font-size: var(--font-size-normal);
        border-left: 3px solid var(--primary-color);
    }
    
    /* History items */
    .history-item {
        padding: 1.5rem;
        background-color: var(--background-card);
        border-radius: var(--border-radius);
        margin-bottom: 1.5rem;
        border-left: 4px solid var(--primary-color);
        box-shadow: var(--box-shadow);
        transition: all 0.3s ease;
    }
    
    .history-item:hover {
        transform: translateY(-2px);
        box-shadow: var(--box-shadow-hover);
    }
    
    .history-actions {
        display: flex;
        justify-content: flex-end;
        margin-top: 1rem;
        gap: 0.5rem;
    }
    
    .date-info {
        color: var(--text-secondary);
        font-size: var(--font-size-small) !important;
        font-style: italic;
    }
    
    /* Inputs and selects */
    .stTextInput > div > div, .stSelectbox > div > div {
        background-color: var(--background-light) !important;
        color: var(--text-color) !important;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color) !important;
        padding: 0.5rem !important;
    }
    
    .stTextInput input, .stSelectbox span, .stSelectbox input {
        color: var(--text-color) !important;
        font-size: var(--font-size-normal) !important;
    }
    
    /* Dropdown options */
    .stSelectbox ul {
        background-color: var(--background-light) !important;
    }
    
    .stSelectbox ul li {
        color: var(--text-color) !important;
    }
    
    /* Tabs styling */
    .stTabs {
        background-color: var(--background-card);
        border-radius: var(--border-radius);
        padding: 1.2rem;
        box-shadow: var(--box-shadow);
    }
    
    .stTab {
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--background-secondary) !important;
        border-radius: var(--border-radius) !important;
        border: none !important;
        color: var(--text-color) !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: var(--font-size-normal) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: var(--text-on-primary) !important;
        font-weight: 600 !important;
    }
    
    /* Button styling */
    .stButton button {
        background-color: var(--primary-color);
        color: var(--text-on-primary);
        border-radius: var(--border-radius);
        border: none;
        box-shadow: var(--box-shadow);
        font-weight: 600;
        transition: all 0.3s ease;
        padding: 0.6rem 1.2rem !important;
        font-size: var(--font-size-normal) !important;
    }
    
    .stButton button:hover {
        background-color: #FFE55C;
        color: var(--text-on-primary); /* Ensure black text on light background */
        transform: translateY(-2px);
        box-shadow: var(--box-shadow-hover);
    }

    /* Secondary button */
    .secondary-btn button {
        background-color: var(--background-secondary) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .secondary-btn button:hover {
        background-color: var(--border-color) !important;
    }
    
    /* Danger button */
    .danger-btn button {
        background-color: #FFF0F0 !important;
        color: #D32F2F !important;
        border: 1px solid #FFCDD2 !important;
    }
    
    .danger-btn button:hover {
        background-color: #FFEBEE !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--background-secondary) !important;
        border-radius: var(--border-radius) !important;
        color: var(--text-color) !important;
        font-weight: 600 !important;
        padding: 0.8rem 1rem !important;
    }
    
    .streamlit-expanderContent {
        background-color: var(--background-card) !important;
        border-radius: 0 0 var(--border-radius) var(--border-radius) !important;
        border: 1px solid var(--background-secondary) !important;
        border-top: none !important;
        padding: 1.2rem !important;
    }
    
    /* Divider */
    hr {
        border-color: var(--border-color);
        margin: 2rem 0 !important;
        height: 2px !important;
    }
    
    /* Radio buttons and checkboxes */
    .stRadio > div, .stCheckbox > div {
        color: var(--text-color) !important;
    }
    
    .stRadio label, .stCheckbox label {
        font-size: var(--font-size-normal) !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: var(--background-secondary) !important;
    }
    
    .stCodeBlock code {
        color: var(--text-color) !important;
        font-size: var(--font-size-normal) !important;
    }
    
    /* Container cards */
    .card-container {
        background-color: var(--background-card);
        border-radius: var(--border-radius);
        padding: 1.8rem;
        box-shadow: var(--box-shadow);
        margin-bottom: 1.8rem;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Warning and error messages */
    .warning-message {
        background-color: #FFF9E6;
        border-left: 4px solid var(--primary-color);
        padding: 1.2rem;
        border-radius: var(--border-radius);
        color: var(--text-color);
        margin: 1.2rem 0;
        font-weight: 500;
    }
    
    .error-message {
        background-color: #FFF0F0;
        border-left: 4px solid #F44336;
        padding: 1.2rem;
        border-radius: var(--border-radius);
        color: var(--text-color);
        margin: 1.2rem 0;
        font-weight: 500;
    }
    
    .success-message {
        background-color: #F1F8E9;
        border-left: 4px solid #4CAF50;
        padding: 1.2rem;
        border-radius: var(--border-radius);
        color: var(--text-color);
        margin: 1.2rem 0;
        font-weight: 500;
    }
    
    /* Data table */
    .stDataFrame {
        background-color: var(--background-card) !important;
    }
    
    .stDataFrame [data-testid="stTable"] {
        background-color: var(--background-light) !important;
    }
    
    .stDataFrame th {
        background-color: var(--background-secondary) !important;
        color: var(--text-color) !important;
        font-weight: 600 !important;
        padding: 0.8rem !important;
        font-size: var(--font-size-normal) !important;
    }
    
    .stDataFrame td {
        background-color: var(--background-light) !important;
        color: var(--text-color) !important;
        padding: 0.8rem !important;
        font-size: var(--font-size-normal) !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}

    /* Selection text and links */
    ::selection {
        background-color: var(--primary-color);
        color: var(--text-on-primary);
    }
    
    a {
        color: #0366D6 !important;
        text-decoration: none !important;
        font-weight: 500;
    }
    
    a:hover {
        text-decoration: underline !important;
        color: #0056B3 !important;
    }
    
    /* Text area enhancements */
    .stTextArea textarea {
        background-color: var(--background-light) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
        font-size: var(--font-size-normal) !important;
        font-family: 'Roboto', sans-serif !important;
        line-height: 1.6;
        padding: 1rem !important;
    }
    
    /* Transcript text styling */
    .transcript-text {
        background-color: var(--background-secondary);
        padding: 1.2rem;
        border-radius: var(--border-radius);
        font-size: var(--font-size-normal) !important;
        font-family: 'Roboto', sans-serif;
        line-height: 1.6;
        color: var(--text-color);
        white-space: pre-wrap;
        overflow-y: auto;
        max-height: 500px;
        border-left: 4px solid var(--primary-color);
    }

    /* Override Streamlit's default header/navbar */
    .stApp {
        background-color: var(--background-light);
    }

    header[data-testid="stHeader"] {
        background-color: white !important;
        border-bottom: 1px solid var(--border-color);
    }

    /* Hide default Streamlit menu and deploy buttons for cleaner look */
    button[kind="header"] {
        display: none !important;
    }

    .stDeployButton {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Check if user is authenticated
if not auth.check_password():
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    with tab2:
        auth.create_account()
    st.stop()  # Stop application flow if not authenticated

# Custom header with logo
st.markdown(
    """
    <div class="app-header">
        <div class="app-logo">EchoScript AI</div>
        <div class="app-subtitle">Transform Audio to Insights</div>
        <div class="app-tagline">Powered by Assembly AI & OpenAI</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Display API key status
st.sidebar.success(f"Using AssemblyAI API key: {assemblyai_api_key[:5]}...")

if openai_api_key:
    st.sidebar.success(f"Using OpenAI API key: {openai_api_key[:5]}...")
else:
    st.sidebar.warning("OpenAI API key not found. GPT analysis will not be available.")

# Add logout button in sidebar
st.sidebar.subheader(f"Welcome, {st.session_state.name}")
if st.sidebar.button("Logout"):
    auth.logout()

# Main navigation
tabs = st.tabs(["Transcribe", "History", "Templates"])

# TRANSCRIBE TAB
with tabs[0]:
    # Sidebar for configuration
    st.sidebar.header("Configuration")

    # Language selection
    language_options = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Dutch": "nl",
        "Hindi": "hi",
        "Japanese": "ja",
        "Chinese": "zh"
    }

    selected_language = st.sidebar.selectbox(
        "Select Language",
        list(language_options.keys()),
        index=0
    )

    # Advanced options
    st.sidebar.subheader("AssemblyAI Features")
    speaker_diarization = st.sidebar.checkbox("Speaker Diarization", 
                                             help="Identify different speakers in the audio")
    auto_chapters = st.sidebar.checkbox("Auto Chapters", 
                                       help="Automatically separate content into chapters")
    entity_detection = st.sidebar.checkbox("Entity Detection", 
                                          help="Detect entities like names, places, etc.")
    content_moderation = st.sidebar.checkbox("Content Moderation", 
                                            help="Flag potentially sensitive content")
    format_text = st.sidebar.checkbox("Format Text", value=True, 
                                     help="Add punctuation and formatting to transcript")

    # OpenAI options
    if openai_api_key:
        st.sidebar.subheader("OpenAI Analysis")
        enable_gpt_analysis = st.sidebar.checkbox("Enable GPT Analysis", value=True,
                                                help="Use OpenAI to analyze the transcript")
        
        # Dictionary mapping friendly names to API model names
        openai_models = {
            "o1": "gpt-4o", 
            "o1-mini": "o1-mini-2024-09-12",
            "o3-mini": "o3-mini-2025-01-31",
            "o1-preview": "o1-preview-2024-09-12",
            "GPT-4o Search Preview": "gpt-4o-search-preview",
            "GPT-4o": "gpt-4o",
            "GPT-4o mini": "gpt-4o-mini",
            "GPT-4 Turbo": "gpt-4-turbo",
            "GPT-4 Vision": "gpt-4-vision-preview",
            "GPT-4": "gpt-4",
            "GPT-3.5 Turbo": "gpt-3.5-turbo",
            "GPT-3.5 Turbo 16k": "gpt-3.5-turbo-16k",
            "Claude 3 Opus": "claude-3-opus-20240229",
            "Claude 3 Sonnet": "claude-3-sonnet-20240229",
            "Claude 3 Haiku": "claude-3-haiku-20240307"
        }
        
        # Dictionary mapping friendly names to their token limits
        model_token_limits = {
            "o1": 16384,
            "o1-mini": 100000,
            "o3-mini": 100000,
            "o1-preview": 100000,
            "GPT-4o Search Preview": 32768,
            "GPT-4o": 16384,
            "GPT-4o mini": 16384,
            "GPT-4 Turbo": 4096,
            "GPT-4 Vision": 4096,
            "GPT-4": 4096,
            "GPT-3.5 Turbo": 4096,
            "GPT-3.5 Turbo 16k": 16384,
            "Claude 3 Opus": 4096,
            "Claude 3 Sonnet": 4096,
            "Claude 3 Haiku": 4096
        }
        
        selected_model = st.sidebar.selectbox(
            "Select OpenAI Model",
            list(openai_models.keys()),
            index=0
        )
        
        # Show model-specific token limit info
        st.sidebar.caption(f"Selected model has approximate max output limit of {model_token_limits[selected_model]} tokens")
        
        # Check if this is a search model or Claude model which don't support temperature
        is_search_model = "search" in openai_models[selected_model].lower()
        is_claude_model = "claude" in openai_models[selected_model].lower()
        temperature_unsupported = is_search_model or is_claude_model
        
        if temperature_unsupported:
            if is_search_model:
                st.sidebar.info("Note: Search models like GPT-4o Search Preview don't support temperature adjustment.")
            elif is_claude_model:
                st.sidebar.info("Note: Claude models don't support temperature adjustment through the OpenAI API.")
        
        # Advanced model parameters
        with st.sidebar.expander("Advanced Model Parameters"):
            # Calculate recommended max for this model
            recommended_max = min(model_token_limits[selected_model], 50000)
            
            max_tokens = st.slider(
                "Max Tokens", 
                min_value=100, 
                max_value=50000, 
                value=min(1500, recommended_max), 
                step=500,
                help="Maximum number of tokens in the GPT response (models vary in their limits)"
            )
            
            # Warning if tokens exceed model capability
            if max_tokens > model_token_limits[selected_model]:
                st.sidebar.warning(f"⚠️ The selected value ({max_tokens}) exceeds the approximate limit of your chosen model ({model_token_limits[selected_model]}). The API may use a lower value.")
            
            # Only show temperature slider for models that support it
            if not temperature_unsupported:
                temperature = st.slider(
                    "Temperature", 
                    min_value=0.0, 
                    max_value=2.0, 
                    value=0.7, 
                    step=0.1,
                    help="Controls randomness: 0=deterministic, 2=maximum creativity"
                )
            else:
                # Create an empty placeholder with a message for models that don't support temperature
                if is_search_model:
                    st.write("Temperature not applicable for search models")
                elif is_claude_model:
                    st.write("Temperature not applicable for Claude models via OpenAI API")
                # Set default temperature which will be ignored anyway
                temperature = 0.7
        
        # Get saved prompt templates for the dropdown
        saved_templates = db.get_prompt_templates()
        
        analysis_types = {
            "Standard Analysis": """
            You're analyzing a transcript from an audio file. Please provide insights on:
            1. Key points and summary
            2. Main topics discussed
            3. Any action items or important information
            
            Here's the transcript:
            {transcript}
            """,
            "Executive Summary": """
            Create a concise executive summary of this transcript. Include:
            - Main purpose/topic of the discussion (1 sentence)
            - 3-5 key takeaways in bullet points
            - Any decisions made or next steps identified
            
            Keep the summary business-appropriate and highlight only the most critical information.
            
            Here's the transcript:
            {transcript}
            """,
            "Meeting Notes": """
            Convert this transcript into organized meeting notes. Include:
            - Meeting objective
            - Key discussion points
            - Decisions made
            - Action items with owners (if mentioned)
            - Follow-up tasks
            
            Format this as a professional meeting summary that could be shared with participants.
            
            Here's the transcript:
            {transcript}
            """
        }
        
        # Add options for saved templates
        template_options = ["Built-in Templates"]
        if saved_templates:
            template_options.append("Saved Templates")
        
        template_source = st.sidebar.radio("Template Source", template_options)
        
        if template_source == "Built-in Templates":
            selected_analysis_type = st.sidebar.selectbox(
                "Analysis Type",
                list(analysis_types.keys()),
                index=0
            )
            prompt_template = analysis_types[selected_analysis_type]
        else:  # Saved Templates
            if saved_templates:
                template_names = [f"{t['name']}" for t in saved_templates]
                selected_template_name = st.sidebar.selectbox(
                    "Select Template",
                    template_names
                )
                
                # Find the selected template
                selected_template = next((t for t in saved_templates if t['name'] == selected_template_name), None)
                if selected_template:
                    prompt_template = selected_template['template_text']
                    
                    # Show template description if available
                    if selected_template['description']:
                        st.sidebar.info(selected_template['description'])
                else:
                    prompt_template = analysis_types["Standard Analysis"]
            else:
                st.sidebar.warning("No saved templates found. Create one in the Templates tab.")
                prompt_template = analysis_types["Standard Analysis"]
        
        # Custom prompt option
        use_custom_prompt = st.sidebar.checkbox("Use Custom Prompt", 
                                               help="Define your own custom prompt for GPT analysis")
        
        if use_custom_prompt:
            custom_prompt = st.sidebar.text_area(
                "Custom Prompt",
                value="Analyze this transcript and provide insights:\n\n{transcript}",
                help="Use {transcript} as a placeholder for the transcribed text"
            )
    else:
        enable_gpt_analysis = False

    # File uploader
    st.header("Upload Your Audio File")
    uploaded_file = st.file_uploader("Choose an audio file", 
                                    type=["mp3", "wav", "m4a", "flac", "mp4", "aac", "wma"],
                                    help="Upload audio files in various formats",
                                    label_visibility="collapsed")

    # Process the file
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / (1024 * 1024):.2f} MB",
            "File type": uploaded_file.type
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("File Details")
            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")
        
        # Add transcript name and comments fields
        st.subheader("Transcript Information")
        transcript_name = st.text_input("Transcript Name (optional)", 
                                      placeholder="Enter a name for this transcript",
                                      help="Providing a name helps identify this transcript in the history")
        
        transcript_comments = st.text_area("Comments (optional)", 
                                        placeholder="Add any notes or comments about this transcript",
                                        help="Add any context or notes about this recording")
        
        # Default transcript name to filename if left empty
        if not transcript_name:
            transcript_name = uploaded_file.name
        
        # Transcription button
        if st.button("🚀 Start Transcription & Analysis"):
            # Save uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name
                
            try:
                st.info("Beginning the transcription process. This may take some time depending on the file size.")
                
                # Prepare configuration options
                config_options = {
                    "language": language_options[selected_language],
                    "speaker_diarization": speaker_diarization,
                    "auto_chapters": auto_chapters,
                    "entity_detection": entity_detection,
                    "content_moderation": content_moderation,
                    "format_text": format_text
                }
                
                # Start transcription
                with st.spinner("Starting transcription process..."):
                    st.write("Sending file to AssemblyAI...")
                    transcript = transcribe_audio(temp_file_path, config_options)
                    
                    if transcript.id:
                        st.success(f"Transcription started! ID: {transcript.id}")
                    else:
                        st.warning("Transcription started but no ID was returned. This might affect tracking.")
                
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Poll for completion
                status_text.text("Transcribing audio... This may take a while for large files.")
                
                # Wait for the transcript to complete
                start_time = time.time()
                while transcript.status != aai.TranscriptStatus.completed:
                    # Check if there was an error
                    if transcript.status == aai.TranscriptStatus.error:
                        st.error(f"Transcription failed: {transcript.error}")
                        break
                    
                    # Update progress bar (based on time elapsed - just a visual indicator)
                    elapsed = time.time() - start_time
                    progress = min(90, int(elapsed / 2))  # Cap at 90% until completion
                    progress_bar.progress(progress)
                    
                    # Update status text
                    status_text.text(f"Transcribing audio... Status: {transcript.status}")
                    
                    # Wait before checking again
                    time.sleep(2)
                    
                    # Refresh the transcript object
                    transcript = aai.Transcript.get_by_id(transcript.id)
                
                # Transcription completed
                if transcript.status == aai.TranscriptStatus.completed:
                    progress_bar.progress(100)
                    status_text.text("Transcription completed!")
                    
                    # Get all transcript data
                    transcript_data = get_transcript_data(transcript)
                    
                    # Save transcription to database
                    transcription_db_id = db.save_transcription(
                        file_name=uploaded_file.name,
                        file_size=uploaded_file.size / (1024 * 1024),  # Convert to MB
                        file_type=uploaded_file.type,
                        transcription_id=transcript.id,
                        language=language_options[selected_language],
                        transcription_text=transcript.text,
                        config_options=config_options,
                        transcript_name=transcript_name,
                        transcript_comments=transcript_comments
                    )
                    
                    st.success(f"Transcription saved to database with ID: {transcription_db_id}")
                    
                    # Initialize tabs for organizing content
                    result_tabs = st.tabs(["Transcript", "Advanced Features", "AI Analysis"])
                    
                    # Transcript tab
                    with result_tabs[0]:
                        st.subheader("Transcription Results")
                        
                        # Create a results container with styling
                        st.markdown('<div class="result-area">', unsafe_allow_html=True)
                        st.write(transcript.text)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Export options
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Export as text
                            if st.download_button(
                                label="Download Transcript (TXT)",
                                data=transcript.text,
                                file_name=f"{uploaded_file.name.split('.')[0]}_transcript.txt",
                                mime="text/plain"
                            ):
                                st.success("Transcript downloaded!")
                        
                        with col2:
                            # Export as JSON if advanced features were used
                            if any([speaker_diarization, auto_chapters, entity_detection]):
                                if st.download_button(
                                    label="Download Full Data (JSON)",
                                    data=json.dumps(transcript_data, indent=2),
                                    file_name=f"{uploaded_file.name.split('.')[0]}_data.json",
                                    mime="application/json"
                                ):
                                    st.success("Full data downloaded!")
                    
                    # Advanced Features tab
                    with result_tabs[1]:
                        if not any([speaker_diarization, auto_chapters, entity_detection]):
                            st.info("No advanced features were enabled. Enable them in the sidebar to see more detailed analysis.")
                            
                        if speaker_diarization and 'utterances' in transcript_data and transcript_data['utterances']:
                            st.subheader("Speaker Diarization")
                            for utterance in transcript_data['utterances']:
                                st.markdown(
                                    f'<div class="speaker-text" style="background-color: {"#e6f3ff" if utterance["speaker"] % 2 == 0 else "#f0f0f0"}">'
                                    f'<strong>Speaker {utterance["speaker"]}:</strong> {utterance["text"]}'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                        
                        if auto_chapters and 'chapters' in transcript_data and transcript_data['chapters']:
                            st.subheader("Auto Chapters")
                            for i, chapter in enumerate(transcript_data['chapters']):
                                st.markdown(
                                    f'<div class="chapter-card">'
                                    f'<h4>Chapter {i+1}: {chapter["headline"]}</h4>'
                                    f'<p>{chapter["summary"]}</p>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                                
                        if entity_detection and 'entities' in transcript_data and transcript_data['entities']:
                            st.subheader("Detected Entities")
                            
                            # Group entities by type
                            entities_by_type = {}
                            for entity in transcript_data['entities']:
                                entity_type = entity['entity_type']
                                if entity_type not in entities_by_type:
                                    entities_by_type[entity_type] = []
                                if entity['text'] not in entities_by_type[entity_type]:
                                    entities_by_type[entity_type].append(entity['text'])
                            
                            # Display entities by type
                            for entity_type, entities in entities_by_type.items():
                                st.write(f"**{entity_type.title()}**")
                                st.markdown(
                                    ''.join([f'<span class="entity-tag">{entity}</span>' for entity in entities]),
                                    unsafe_allow_html=True
                                )
                    
                    # AI Analysis tab
                    with result_tabs[2]:
                        if enable_gpt_analysis and openai_api_key:
                            st.subheader("GPT Analysis")
                            
                            with st.spinner("Analyzing transcript with OpenAI..."):
                                try:
                                    # Debug output for transcript
                                    st.write(f"Debug: Transcript length is {len(transcript.text) if hasattr(transcript, 'text') and transcript.text else 0} characters")
                                    
                                    # Determine which prompt to use
                                    if use_custom_prompt:
                                        prompt_template_to_use = custom_prompt
                                    else:
                                        prompt_template_to_use = prompt_template
                                    
                                    # Debug output for prompt template
                                    st.write(f"Debug: Using {'custom' if use_custom_prompt else 'standard'} prompt template")
                                    st.write(f"Debug: Prompt template contains placeholder: {'{transcript}' in prompt_template_to_use}")
                                    
                                    # Fix: Ensure the prompt template has the {transcript} placeholder
                                    if '{transcript}' not in prompt_template_to_use:
                                        st.warning("Warning: Prompt template doesn't contain {transcript} placeholder. Adding it now.")
                                        prompt_template_to_use = prompt_template_to_use + "\n\nHere's the transcript:\n{transcript}"
                                    
                                    # Get the model ID
                                    model_id = openai_models[selected_model]
                                    
                                    # Check if this is a search model or Claude model which don't support temperature
                                    is_search_model = "search" in model_id.lower()
                                    is_claude_model = "claude" in model_id.lower()
                                    temperature_unsupported = is_search_model or is_claude_model
                                    
                                    if temperature_unsupported:
                                        if is_search_model:
                                            st.info("Note: Search models like GPT-4o Search Preview don't support temperature adjustment.")
                                        elif is_claude_model:
                                            st.info("Note: Claude models don't support temperature adjustment through the OpenAI API.")
                                    
                                    # Analyze with GPT
                                    st.write("Debug: Sending transcript to GPT for analysis...")
                                    
                                    # Don't pass temperature parameter for search models and Claude models
                                    if temperature_unsupported:
                                        st.write("Debug: Using configuration without temperature parameter")
                                        gpt_analysis = analyze_transcript_with_gpt(
                                            transcript.text, 
                                            prompt_template=prompt_template_to_use,
                                            model=model_id,
                                            max_tokens=max_tokens
                                        )
                                    else:
                                        st.write("Debug: Using standard model configuration (with temperature)")
                                        gpt_analysis = analyze_transcript_with_gpt(
                                            transcript.text, 
                                            prompt_template=prompt_template_to_use,
                                            model=model_id,
                                            max_tokens=max_tokens,
                                            temperature=temperature
                                        )
                                    
                                    # Save analysis to database
                                    token_usage = 0  # We don't have usage info in the new return format
                                    db.save_analysis(
                                        transcription_db_id=transcription_db_id,
                                        model=gpt_analysis["model"],
                                        analysis_text=gpt_analysis["analysis"],
                                        prompt_template=prompt_template_to_use,
                                        token_usage=token_usage
                                    )
                                    
                                    # Display the analysis
                                    st.markdown('<div class="gpt-analysis">', unsafe_allow_html=True)
                                    st.markdown(gpt_analysis["analysis"])
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Display any citations if available
                                    if "citations" in gpt_analysis and gpt_analysis["citations"]:
                                        st.subheader("Sources & Citations")
                                        for i, citation in enumerate(gpt_analysis["citations"]):
                                            st.markdown(
                                                f'<div class="gpt-citation">'
                                                f'<strong>[{i+1}]</strong> {citation.get("title", "Source")}'
                                                f'</div>',
                                                unsafe_allow_html=True
                                            )
                                    
                                    # Show token usage information
                                    if "usage" in gpt_analysis and gpt_analysis["usage"]:
                                        st.caption(f"Token usage: {gpt_analysis['usage']['total_tokens']} tokens")
                                    
                                    # Allow downloading the analysis
                                    if st.download_button(
                                        label="Download Analysis (TXT)",
                                        data=gpt_analysis["analysis"],
                                        file_name=f"{uploaded_file.name.split('.')[0]}_analysis.txt",
                                        mime="text/plain"
                                    ):
                                        st.success("Analysis downloaded!")
                                    
                                except Exception as e:
                                    st.error(f"OpenAI analysis failed: {str(e)}")
                                    st.info("Check your OpenAI API key in your .env file and try again.")
                        else:
                            if not openai_api_key:
                                st.warning("OpenAI API key not found. Please add your key to the .env file to enable GPT analysis.")
                            else:
                                st.info("GPT Analysis is disabled. Enable it in the sidebar to analyze the transcript.")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("If you're seeing API-related errors, check your API keys and make sure the services are working properly.")
            
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

# HISTORY TAB
with tabs[1]:
    st.header("Transcription History")
    st.write("View your past transcriptions and analyses or create new analyses")
    
    # Get all transcriptions from the database
    transcriptions = db.get_all_transcriptions()
    
    # If no transcriptions, show info message
    if not transcriptions:
        st.info("No transcription history found. Start by transcribing an audio file.")
    else:
        # Display each transcription in a card
        for transcription in transcriptions:
            # Use transcript_name if available, otherwise use file_name
            display_name = transcription.get('transcript_name', transcription['file_name']) or transcription['file_name']
            
            with st.expander(f"{display_name} ({transcription['created_at']})"):
                st.markdown(f"<div class='history-item'>", unsafe_allow_html=True)
                
                # Metadata
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**File:** {transcription['file_name']}")
                    st.write(f"**Size:** {transcription['file_size']:.2f} MB")
                    st.write(f"**Language:** {transcription['language']}")
                    
                    # Show comments if available
                    if transcription.get('transcript_comments'):
                        st.write("**Comments:**")
                        st.info(transcription['transcript_comments'])
                
                with col2:
                    # Format the date if it's a string
                    created_at = transcription['created_at']
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    st.write(f"**Created:** {created_at}")
                    st.write(f"**Assembly AI ID:** {transcription['transcription_id']}")
                
                # Preview text
                st.subheader("Preview")
                st.markdown(f"<div class='result-area'>{transcription['preview_text']}...</div>", unsafe_allow_html=True)
                
                # Get the full transcription
                full_transcription = db.get_transcription(transcription['id'])
                
                # Display the full text button
                view_full_key = f"view_full_{transcription['id']}"
                if st.button(f"View Full Transcription #{transcription['id']}", key=view_full_key):
                    if full_transcription:
                        st.markdown("<div class='result-area'>", unsafe_allow_html=True)
                        st.write(full_transcription['transcription_text'])
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Get analyses for this transcription
                analyses = db.get_analyses_for_transcription(transcription['id'])
                
                if analyses:
                    st.subheader("AI Analyses")
                    
                    for i, analysis in enumerate(analyses):
                        st.markdown(f"<strong>Analysis {i+1}:</strong> {analysis['model']} ({analysis['created_at']})", unsafe_allow_html=True)
                        
                        view_analysis_key = f"view_analysis_{analysis['id']}"
                        if st.button(f"View Analysis #{analysis['id']}", key=view_analysis_key):
                            st.markdown("<div class='gpt-analysis'>", unsafe_allow_html=True)
                            st.write(analysis['analysis_text'])
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.caption(f"Token usage: {analysis['token_usage']} tokens")
                else:
                    st.info("No AI analyses found for this transcription.")
                
                # New Analysis section if OpenAI API key is available
                if openai_api_key:
                    st.subheader("Create New AI Analysis")
                    
                    # Use checkbox to show/hide analysis options instead of an expander
                    show_analysis_options = st.checkbox("Show Analysis Options", 
                                                       key=f"show_options_{transcription['id']}")
                    
                    if show_analysis_options:
                        # Model selection
                        openai_models = {
                            "o1": "gpt-4o", 
                            "o1-mini": "o1-mini-2024-09-12",
                            "o3-mini": "o3-mini-2025-01-31",
                            "o1-preview": "o1-preview-2024-09-12",
                            "GPT-4o Search Preview": "gpt-4o-search-preview",
                            "GPT-4o": "gpt-4o",
                            "GPT-4o mini": "gpt-4o-mini",
                            "GPT-4 Turbo": "gpt-4-turbo",
                            "GPT-4 Vision": "gpt-4-vision-preview",
                            "GPT-4": "gpt-4",
                            "GPT-3.5 Turbo": "gpt-3.5-turbo",
                            "GPT-3.5 Turbo 16k": "gpt-3.5-turbo-16k",
                            "Claude 3 Opus": "claude-3-opus-20240229",
                            "Claude 3 Sonnet": "claude-3-sonnet-20240229",
                            "Claude 3 Haiku": "claude-3-haiku-20240307"
                        }
                        
                        selected_model = st.selectbox(
                            "Select OpenAI Model",
                            list(openai_models.keys()),
                            index=0,
                            key=f"model_select_{transcription['id']}"
                        )
                        
                        # Show model-specific token limit info
                        st.caption(f"Selected model has approximate max output limit of {model_token_limits[selected_model]} tokens")
                        
                        # Add advanced parameters - using columns instead of expander to avoid nesting
                        st.markdown("### Advanced Model Parameters")
                        
                        # Calculate recommended max for this model
                        history_recommended_max = min(model_token_limits[selected_model], 50000)
                        
                        # Check if this is a search model or Claude model which don't support temperature
                        is_search_model = "search" in openai_models[selected_model].lower()
                        is_claude_model = "claude" in openai_models[selected_model].lower()
                        temperature_unsupported = is_search_model or is_claude_model
                        
                        if temperature_unsupported:
                            if is_search_model:
                                st.info("Note: Search models like GPT-4o Search Preview don't support temperature adjustment.")
                            elif is_claude_model:
                                st.info("Note: Claude models don't support temperature adjustment through the OpenAI API.")
                        
                        adv_col1, adv_col2 = st.columns(2)
                        with adv_col1:
                            history_max_tokens = st.slider(
                                "Max Tokens", 
                                min_value=100, 
                                max_value=50000, 
                                value=min(1500, history_recommended_max), 
                                step=500,
                                help="Maximum number of tokens in the GPT response",
                                key=f"max_tokens_{transcription['id']}"
                            )
                            
                            # Warning if tokens exceed model capability
                            if history_max_tokens > model_token_limits[selected_model]:
                                st.warning(f"⚠️ The selected value ({history_max_tokens}) exceeds the approximate limit of your chosen model ({model_token_limits[selected_model]}). The API may use a lower value.")
                        
                        with adv_col2:
                            # Only show temperature slider for models that support it
                            if not temperature_unsupported:
                                history_temperature = st.slider(
                                    "Temperature", 
                                    min_value=0.0, 
                                    max_value=2.0, 
                                    value=0.7, 
                                    step=0.1,
                                    help="Controls randomness in response generation",
                                    key=f"temperature_{transcription['id']}"
                                )
                            else:
                                # Create an empty placeholder with a message for models that don't support temperature
                                if is_search_model:
                                    st.write("Temperature not applicable for search models")
                                elif is_claude_model:
                                    st.write("Temperature not applicable for Claude models via OpenAI API")
                                # Set default temperature which will be ignored anyway
                                history_temperature = 0.7
                        
                        # Get saved templates
                        saved_templates = db.get_prompt_templates()
                        
                        # Template source selection
                        template_options = ["Built-in Templates"]
                        if saved_templates:
                            template_options.append("Saved Templates")
                        
                        template_source = st.radio(
                            "Template Source", 
                            template_options,
                            key=f"template_source_{transcription['id']}"
                        )
                        
                        # Analysis type selection
                        analysis_types = {
                            "Standard Analysis": """
                            You're analyzing a transcript from an audio file. Please provide insights on:
                            1. Key points and summary
                            2. Main topics discussed
                            3. Any action items or important information
                            
                            Here's the transcript:
                            {transcript}
                            """,
                            "Executive Summary": """
                            Create a concise executive summary of this transcript. Include:
                            - Main purpose/topic of the discussion (1 sentence)
                            - 3-5 key takeaways in bullet points
                            - Any decisions made or next steps identified
                            
                            Keep the summary business-appropriate and highlight only the most critical information.
                            
                            Here's the transcript:
                            {transcript}
                            """,
                            "Meeting Notes": """
                            Convert this transcript into organized meeting notes. Include:
                            - Meeting objective
                            - Key discussion points
                            - Decisions made
                            - Action items with owners (if mentioned)
                            - Follow-up tasks
                            
                            Format this as a professional meeting summary that could be shared with participants.
                            
                            Here's the transcript:
                            {transcript}
                            """,
                            "Key Questions": """
                            Based on this transcript, identify:
                            1. What are the 5 most important questions that arise from this content?
                            2. What potential answers or insights can be derived for each question?
                            3. What follow-up information might be needed?
                            
                            Here's the transcript:
                            {transcript}
                            """,
                            "Technical Analysis": """
                            Provide a technical analysis of this transcript, focusing on:
                            1. Technical concepts, terms, or jargon mentioned
                            2. Technical challenges or solutions discussed
                            3. Technical recommendations or best practices identified
                            
                            Organize your response by technical topic and provide explanations for any complex terms.
                            
                            Here's the transcript:
                            {transcript}
                            """
                        }
                        
                        if template_source == "Built-in Templates":
                            selected_analysis_type = st.selectbox(
                                "Analysis Type",
                                list(analysis_types.keys()),
                                index=0,
                                key=f"analysis_type_{transcription['id']}"
                            )
                            custom_prompt = analysis_types[selected_analysis_type]
                        else:  # Saved Templates
                            if saved_templates:
                                template_names = [f"{t['name']}" for t in saved_templates]
                                selected_template_name = st.selectbox(
                                    "Select Template",
                                    template_names,
                                    key=f"saved_template_{transcription['id']}"
                                )
                                
                                # Find the selected template
                                selected_template = next((t for t in saved_templates if t['name'] == selected_template_name), None)
                                if selected_template:
                                    custom_prompt = selected_template['template_text']
                                    
                                    # Show template description if available
                                    if selected_template['description']:
                                        st.info(selected_template['description'])
                                else:
                                    custom_prompt = analysis_types["Standard Analysis"]
                            else:
                                st.warning("No saved templates found. Create one in the Templates tab.")
                                custom_prompt = analysis_types["Standard Analysis"]
                        
                        # Custom prompt option
                        use_custom_prompt = st.checkbox(
                            "Edit Template", 
                            help="Edit the selected template for this analysis only",
                            key=f"use_custom_{transcription['id']}"
                        )
                        
                        if use_custom_prompt:
                            custom_prompt = st.text_area(
                                "Custom Prompt",
                                value=custom_prompt,
                                help="Use {transcript} as a placeholder for the transcribed text",
                                key=f"custom_prompt_{transcription['id']}"
                            )
                    else:
                        # Default values when options are hidden
                        selected_model = "GPT-4"
                        custom_prompt = analysis_types["Standard Analysis"]
                        use_custom_prompt = False
                        # Set default values for max_tokens and temperature
                        history_max_tokens = 1500
                        history_temperature = 0.7
                    
                    # Run analysis button
                    run_analysis_key = f"run_analysis_{transcription['id']}"
                    if st.button("Run New Analysis", key=run_analysis_key):
                        if full_transcription:
                            with st.spinner("Running new analysis with OpenAI..."):
                                try:
                                    # Determine which prompt to use
                                    if use_custom_prompt:
                                        prompt_template_to_use = custom_prompt
                                    else:
                                        if template_source == "Built-in Templates":
                                            prompt_template_to_use = analysis_types[selected_analysis_type]
                                        else:
                                            # Get template from saved templates
                                            prompt_template_to_use = custom_prompt
                                    
                                    # Debug output for transcript and prompt template
                                    st.write(f"Debug: Transcript length is {len(full_transcription['transcription_text']) if full_transcription and 'transcription_text' in full_transcription else 0} characters")
                                    st.write(f"Debug: Using prompt template: {prompt_template_to_use[:100]}...")
                                    
                                    # Fix: Ensure the prompt template has the {transcript} placeholder
                                    if '{transcript}' not in prompt_template_to_use:
                                        st.warning("Warning: Prompt template doesn't contain {transcript} placeholder. Adding it now.")
                                        prompt_template_to_use = prompt_template_to_use + "\n\nHere's the transcript:\n{transcript}"
                                    
                                    # More detailed transcript debugging
                                    if not full_transcription:
                                        st.error("Error: Failed to retrieve transcription from database")
                                    elif 'transcription_text' not in full_transcription:
                                        st.error(f"Error: 'transcription_text' not found in transcription data. Available keys: {list(full_transcription.keys())}")
                                    elif not full_transcription['transcription_text']:
                                        st.error("Error: 'transcription_text' is empty")
                                    else:
                                        # Get the model ID
                                        model_id = openai_models[selected_model]
                                        
                                        # Check if this is a search model or Claude model which don't support temperature
                                        is_search_model = "search" in model_id.lower()
                                        is_claude_model = "claude" in model_id.lower()
                                        temperature_unsupported = is_search_model or is_claude_model
                                        
                                        if temperature_unsupported:
                                            if is_search_model:
                                                st.info("Note: Search models like GPT-4o Search Preview don't support temperature adjustment.")
                                            elif is_claude_model:
                                                st.info("Note: Claude models don't support temperature adjustment through the OpenAI API.")
                                        
                                        # Try formatting the prompt first to check for errors
                                        try:
                                            formatted_prompt = prompt_template_to_use.format(transcript=full_transcription['transcription_text'][:100] + "...")
                                            st.write(f"Debug: Format test successful, formatted prompt begins with: {formatted_prompt[:100]}...")
                                        except Exception as e:
                                            st.error(f"Debug: Error formatting prompt template: {str(e)}")
                                            raise e
                                            
                                        st.write(f"Debug: About to run analysis with model: {model_id}, is_search_model: {is_search_model}")
                                        
                                        # Don't pass temperature parameter for search models and Claude models
                                        try:
                                            if temperature_unsupported:
                                                st.write("Debug: Using configuration without temperature parameter")
                                                st.write(f"Debug: About to send transcript with {len(full_transcription['transcription_text'])} characters to GPT")
                                                st.write(f"Debug: Prompt template: {prompt_template_to_use[:100]}...")
                                                
                                                gpt_analysis = analyze_transcript_with_gpt(
                                                    full_transcription['transcription_text'], 
                                                    prompt_template=prompt_template_to_use,
                                                    model=model_id,
                                                    max_tokens=history_max_tokens
                                                )
                                            else:
                                                st.write("Debug: Using standard model configuration (with temperature)")
                                                st.write(f"Debug: About to send transcript with {len(full_transcription['transcription_text'])} characters to GPT")
                                                st.write(f"Debug: Prompt template: {prompt_template_to_use[:100]}...")
                                                
                                                gpt_analysis = analyze_transcript_with_gpt(
                                                    full_transcription['transcription_text'], 
                                                    prompt_template=prompt_template_to_use,
                                                    model=model_id,
                                                    max_tokens=history_max_tokens,
                                                    temperature=history_temperature
                                                )
                                        
                                            st.write("Debug: Analysis completed successfully. Result length: " + str(len(gpt_analysis["analysis"])))
                                            
                                            # Save analysis to database
                                            token_usage = 0
                                            if "usage" in gpt_analysis and gpt_analysis["usage"]:
                                                token_usage = gpt_analysis["usage"]["total_tokens"]
                                                
                                            analysis_id = db.save_analysis(
                                                transcription_db_id=transcription['id'],
                                                model=gpt_analysis["model"],
                                                analysis_text=gpt_analysis["analysis"],
                                                prompt_template=prompt_template_to_use,
                                                token_usage=token_usage
                                            )
                                            
                                            st.success(f"New analysis created successfully with ID: {analysis_id}")
                                            
                                            # Display the analysis
                                            st.subheader("New Analysis Results")
                                            st.markdown('<div class="gpt-analysis">', unsafe_allow_html=True)
                                            st.markdown(gpt_analysis["analysis"])
                                            st.markdown('</div>', unsafe_allow_html=True)
                                            
                                            # Display token usage information (if available)
                                            if "usage" in gpt_analysis and gpt_analysis["usage"]:
                                                st.caption(f"Token usage: {gpt_analysis['usage']['total_tokens']} tokens")
                                            else:
                                                st.caption("Token usage information not available")
                                            
                                            # Allow downloading the analysis
                                            if st.download_button(
                                                label="Download Analysis (TXT)",
                                                data=gpt_analysis["analysis"],
                                                file_name=f"new_analysis_{analysis_id}.txt",
                                                mime="text/plain",
                                                key=f"download_new_{analysis_id}"
                                            ):
                                                st.success("Analysis downloaded!")
                                        except Exception as e:
                                            st.error(f"Analysis failed: {str(e)}")
                                    import traceback
                                    st.error(f"Traceback: {traceback.format_exc()}")
                                
                                except Exception as e:
                                    st.error(f"OpenAI analysis failed: {str(e)}")
                                    import traceback
                                    st.error(f"Traceback: {traceback.format_exc()}")
                        else:
                            st.error("Failed to retrieve full transcription data")
                
                # Delete button
                delete_key = f"delete_{transcription['id']}"
                if st.button(f"Delete Transcription #{transcription['id']}", key=delete_key):
                    if db.delete_transcription(transcription['id']):
                        st.success(f"Transcription #{transcription['id']} deleted successfully!")
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

# Footer with information
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888;">
    <p>Created with Streamlit, Assembly AI, and OpenAI</p>
    <p>For large audio files, the transcription may take several minutes.</p>
</div>
""", unsafe_allow_html=True)

# TEMPLATES TAB
with tabs[2]:
    st.header("Prompt Templates")
    st.write("Create and manage custom prompt templates for AI analysis")
    
    # Create two columns: left for template list, right for template editor
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Template Library")
        
        # Get all templates
        templates = db.get_prompt_templates()
        
        # Add option to create a new template
        if st.button("➕ Create New Template", key="create_new_template"):
            st.session_state["editing_template"] = {
                "id": None,
                "name": "",
                "description": "",
                "template_text": "Analyze this transcript and provide insights on:\n\n{transcript}"
            }
        
        # Display existing templates
        if templates:
            st.write("Select a template to edit:")
            for template in templates:
                if st.button(f"📝 {template['name']}", key=f"edit_template_{template['id']}"):
                    st.session_state["editing_template"] = template
        else:
            st.info("No saved templates yet. Create your first template!")
    
    with col2:
        st.subheader("Template Editor")
        
        # Check if we're editing a template
        if "editing_template" in st.session_state and st.session_state["editing_template"] is not None:
            template = st.session_state["editing_template"]
            
            # Template name
            template_name = st.text_input(
                "Template Name",
                value=template.get("name", ""),
                key="template_name_input"
            )
            
            # Template description
            template_description = st.text_area(
                "Description (optional)",
                value=template.get("description", ""),
                key="template_description_input",
                help="Briefly describe what this template is designed for"
            )
            
            # Template text
            template_text = st.text_area(
                "Template Text",
                value=template.get("template_text", ""),
                height=300,
                key="template_text_input",
                help="Use {transcript} as a placeholder for the transcribed text"
            )
            
            # Show example usage
            with st.expander("How to use prompt templates"):
                st.markdown("""
                - Use `{transcript}` anywhere in your template where you want the transcribed text to be inserted.
                - Structure your prompt to get the most useful AI-generated analysis.
                - Good templates are clear about the format and content you want in the response.
                """)
                
                st.markdown("**Examples of effective prompt patterns:**")
                st.code("""
# Structured analysis
Analyze this transcript and provide:
1. A brief summary (2-3 sentences)
2. Key topics discussed (bullet points)
3. Action items mentioned
4. Questions raised that need follow-up

Transcript:
{transcript}
                """)
                
                st.code("""
# Role-based analysis
You are a business consultant analyzing a meeting transcript.
Identify:
- Strategic initiatives discussed
- Potential risks mentioned
- Resource allocation decisions
- Follow-up actions and responsibilities

Meeting transcript:
{transcript}
                """)
            
            # Buttons for save/update and delete
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                save_button = st.button(
                    "💾 Save Template", 
                    key="save_template_button",
                    type="primary"
                )
                
                if save_button:
                    if not template_name:
                        st.error("Template name is required")
                    elif not template_text:
                        st.error("Template text is required")
                    elif "{transcript}" not in template_text:
                        st.error("Template must include {transcript} placeholder")
                    else:
                        # Save or update template
                        if template.get("id"):
                            # Update existing template
                            db.update_prompt_template(
                                template["id"],
                                template_name,
                                template_text,
                                template_description
                            )
                            st.success(f"Template '{template_name}' updated successfully!")
                        else:
                            # Create new template
                            template_id = db.save_prompt_template(
                                template_name,
                                template_text,
                                template_description
                            )
                            st.session_state["editing_template"]["id"] = template_id
                            st.success(f"Template '{template_name}' created successfully!")
                        
                        # Refresh the page to show updated template list
                        st.rerun()
            
            with col2:
                test_button = st.button(
                    "🧪 Test Template",
                    key="test_template_button"
                )
                
                if test_button:
                    if not template_text:
                        st.error("Template text is required")
                    elif "{transcript}" not in template_text:
                        st.error("Template must include {transcript} placeholder")
                    else:
                        # Create an expander for test options
                        with st.expander("Test Options", expanded=True):
                            # Option to use real GPT or just a preview
                            test_type = st.radio(
                                "Test Method",
                                ["Preview Only", "Test with GPT"],
                                index=0
                            )
                            
                            # Sample transcript or real one
                            sample_options = ["Sample Text"]
                            
                            # Add transcriptions from the database if any
                            transcriptions = db.get_transcriptions()
                            if transcriptions:
                                sample_options.extend([f"Transcription #{t['id']}" for t in transcriptions])
                            
                            transcript_source = st.selectbox(
                                "Transcript Source",
                                sample_options
                            )
                            
                            # If testing with GPT, show model selection
                            if test_type == "Test with GPT":
                                # Model selection
                                test_model = st.selectbox(
                                    "Model",
                                    list(openai_models.keys()),
                                    index=0
                                )
                                
                                # Show model-specific token limit info
                                st.caption(f"Selected model has approximate max output limit of {model_token_limits[test_model]} tokens")
                                
                                # Check if this is a search model or Claude model which don't support temperature
                                is_search_model = "search" in openai_models[test_model].lower()
                                is_claude_model = "claude" in openai_models[test_model].lower()
                                temperature_unsupported = is_search_model or is_claude_model
                                
                                if temperature_unsupported:
                                    if is_search_model:
                                        st.info("Note: Search models like GPT-4o Search Preview don't support temperature adjustment.")
                                    elif is_claude_model:
                                        st.info("Note: Claude models don't support temperature adjustment through the OpenAI API.")
                                
                                # Advanced parameters
                                test_col1, test_col2 = st.columns(2)
                                with test_col1:
                                    # Calculate recommended max for this model
                                    recommended_test_max = min(model_token_limits[test_model], 50000)
                                    
                                    test_max_tokens = st.slider(
                                        "Max Tokens", 
                                        min_value=100, 
                                        max_value=50000, 
                                        value=min(1500, recommended_test_max), 
                                        step=500,
                                        help="Maximum number of tokens in the response"
                                    )
                                    
                                    # Warning if tokens exceed model capability
                                    if test_max_tokens > model_token_limits[test_model]:
                                        st.warning(f"⚠️ The selected value ({test_max_tokens}) exceeds the approximate limit of your chosen model ({model_token_limits[test_model]}). The API may use a lower value.")
                                
                                with test_col2:
                                    # Only show temperature slider for models that support it
                                    if not temperature_unsupported:
                                        test_temperature = st.slider(
                                            "Temperature", 
                                            min_value=0.0, 
                                            max_value=2.0, 
                                            value=0.7, 
                                            step=0.1
                                        )
                                    else:
                                        # Create an empty placeholder with a message for models that don't support temperature
                                        if is_search_model:
                                            st.write("Temperature not applicable for search models")
                                        elif is_claude_model:
                                            st.write("Temperature not applicable for Claude models via OpenAI API")
                                        # Set default temperature which will be ignored anyway
                                        test_temperature = 0.7
                        
                        # Get the transcript text based on the selection
                        if transcript_source == "Sample Text":
                            sample_transcript = "This is a sample transcript. It would normally contain the actual content from your audio file."
                        else:
                            # Extract the transcription ID from the selection
                            selected_id = int(transcript_source.split("#")[1])
                            full_transcription = db.get_transcription(selected_id)
                            if full_transcription and 'transcription_text' in full_transcription:
                                sample_transcript = full_transcription['transcription_text']
                                st.info(f"Using transcription #{selected_id} ({len(sample_transcript)} characters)")
                            else:
                                st.error("Failed to retrieve transcription")
                                sample_transcript = "Error: Could not retrieve transcription data."
                        
                        # Show preview or test with GPT
                        st.subheader("Test Results")
                        if test_type == "Preview Only":
                            # Show a preview with sample text
                            preview = template_text.replace("{transcript}", sample_transcript)
                            st.markdown(f'<div class="result-area">{preview}</div>', unsafe_allow_html=True)
                        else:
                            # Test with GPT
                            with st.spinner("Testing template with GPT..."):
                                try:
                                    model_id = openai_models[test_model]
                                    
                                    # Check if this is a search model or Claude model which don't support temperature
                                    is_search_model = "search" in model_id.lower()
                                    is_claude_model = "claude" in model_id.lower()
                                    temperature_unsupported = is_search_model or is_claude_model
                                    
                                    if temperature_unsupported:
                                        if is_search_model:
                                            st.info("Note: Search models like GPT-4o Search Preview don't support temperature adjustment.")
                                        elif is_claude_model:
                                            st.info("Note: Claude models don't support temperature adjustment through the OpenAI API.")
                                    
                                    # Don't pass temperature parameter for search models and Claude models
                                    try:
                                        # More extensive preprocessing check
                                        try:
                                            formatted_prompt = template_text.format(transcript=sample_transcript[:100] + "...")
                                            st.write(f"Debug: Format test successful, formatted prompt begins with: {formatted_prompt[:100]}...")
                                        except Exception as e:
                                            st.error(f"Debug: Error formatting prompt template: {str(e)}")
                                            raise e
                                            
                                        if temperature_unsupported:
                                            st.write("Debug: Using configuration without temperature parameter")
                                            st.write(f"Debug: About to send transcript with {len(sample_transcript)} characters to GPT")
                                            st.write(f"Debug: Prompt template: {template_text[:100]}...")
                                            
                                            gpt_analysis = analyze_transcript_with_gpt(
                                                sample_transcript, 
                                                prompt_template=template_text,
                                                model=model_id,
                                                max_tokens=test_max_tokens
                                            )
                                        else:
                                            st.write("Debug: Using standard model configuration (with temperature)")
                                            st.write(f"Debug: About to send transcript with {len(sample_transcript)} characters to GPT")
                                            st.write(f"Debug: Prompt template: {template_text[:100]}...")
                                            
                                            gpt_analysis = analyze_transcript_with_gpt(
                                                sample_transcript, 
                                                prompt_template=template_text,
                                                model=model_id,
                                                max_tokens=test_max_tokens,
                                                temperature=test_temperature
                                            )
                                        
                                        # Display the response
                                        st.markdown('<div class="gpt-analysis">', unsafe_allow_html=True)
                                        st.markdown(gpt_analysis["analysis"])
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    except Exception as e:
                                        st.error(f"GPT analysis failed: {str(e)}")
                                    st.info("Check your OpenAI API key in your .env file and try again.")
                                
                                except Exception as e:
                                    st.error(f"GPT analysis failed: {str(e)}")
                                    st.info("Check your OpenAI API key in your .env file and try again.")
            
            with col3:
                # Only show delete button for existing templates
                if template.get("id"):
                    delete_button = st.button(
                        "🗑️ Delete Template",
                        key="delete_template_button"
                    )
                    
                    if delete_button:
                        if st.checkbox(f"Confirm deletion of '{template_name}'", key="confirm_delete"):
                            db.delete_prompt_template(template["id"])
                            st.success(f"Template '{template_name}' deleted successfully!")
                            del st.session_state["editing_template"]
                            st.rerun()
        else:
            # No template being edited
            st.info("Select a template from the library or create a new one to start editing.")

# Initialize some session state for the templates tab
if 'editing_template' not in st.session_state:
    st.session_state["editing_template"] = {
        "id": None,
        "name": "",
        "description": "",
        "template_text": "Analyze this transcript and provide insights on:\n\n{transcript}"
    } 