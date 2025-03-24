# EchoScript AI

A modern audio transcription and analysis application powered by AssemblyAI and OpenAI with secure user accounts.

## Features

- **Audio Transcription**: Convert audio files to text with high accuracy
- **Multiple Languages**: Support for transcription in 10+ languages
- **AI-Powered Analysis**: Analyze transcripts with GPT models
- **User Authentication**: Secure login and account management
- **File Management**: Upload, store, and manage audio files and transcriptions
- **Custom Analysis Templates**: Create and save custom prompt templates
- **Clean, Modern UI**: User-friendly interface with intuitive controls

## Screenshots

(Add your screenshots here)

## Requirements

- Python 3.7 or higher
- AssemblyAI API key (sign up at [AssemblyAI](https://www.assemblyai.com/))
- OpenAI API key (sign up at [OpenAI](https://platform.openai.com/))

## Local Development Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/echoscript-ai.git
   cd echoscript-ai
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your API keys:
   ```
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Run the application
   ```
   streamlit run app.py
   ```

6. Open your browser at `http://localhost:8501`

## Deploying to Streamlit Cloud

1. Push your code to a GitHub repository

2. Sign up for [Streamlit Cloud](https://streamlit.io/cloud)

3. Create a new app and select your GitHub repository

4. Set the main file path to `app.py`

5. In the advanced settings, add your secrets:
   - `assemblyai_api_key`
   - `openai_api_key`
   
6. Deploy your app

## Project Structure

```
echoscript-ai/
├── app.py             # Main application file
├── auth.py            # Authentication functionality
├── database.py        # Database operations
├── utils.py           # Utility functions
├── .env               # Environment variables (local dev)
├── requirements.txt   # Project dependencies
├── .streamlit/        # Streamlit configuration
│   └── secrets.toml   # Secret configuration for deployment
└── data/              # Data directory (created on first run)
    └── transcription_history.db  # SQLite database file
```

## Default Login

On first run, a default admin user is created:
- Username: `admin`
- Password: `admin123`

**Important**: Change the default password after logging in for security!

## User Management

- New users can register through the Create Account form
- Each user has their own private transcriptions and templates

## License

(Add your license here)

## Acknowledgements

- [Streamlit](https://streamlit.io/) - The web framework used
- [AssemblyAI](https://www.assemblyai.com/) - Transcription API
- [OpenAI](https://openai.com/) - AI analysis capabilities 