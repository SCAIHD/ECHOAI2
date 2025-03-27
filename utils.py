import os
import time
import json
import assemblyai as aai
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment variables
assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not assemblyai_api_key:
    raise ValueError("ASSEMBLYAI_API_KEY not found in environment variables")

# Configure the AssemblyAI API key
aai.settings.api_key = assemblyai_api_key

# Configure OpenAI client if API key is available
openai_client = None
if openai_api_key:
    openai_client = openai.OpenAI(api_key=openai_api_key)

def upload_file(file_path):
    """
    Prepare a file for AssemblyAI transcription.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        str: Path to the audio file
    """
    # In newer versions of AssemblyAI, file upload is handled automatically
    return file_path

def transcribe_audio(audio_path, config_options=None):
    """
    Transcribe an audio file using AssemblyAI with advanced features.
    
    Args:
        audio_path (str): Path to the audio file
        config_options (dict): Configuration options for transcription
            - language (str): Language code (e.g., 'en', 'es')
            - speaker_diarization (bool): Enable speaker diarization
            - auto_chapters (bool): Enable auto chapters
            - entity_detection (bool): Enable entity detection
            - content_moderation (bool): Enable content moderation
            - format_text (bool): Enable text formatting
        
    Returns:
        aai.Transcript: Transcript object
    """
    try:
        # Create a default config
        config = aai.TranscriptionConfig()
        
        # Apply advanced options if provided
        if config_options:
            # Language selection
            if config_options.get('language'):
                config.language_code = config_options['language']
            
            # Speaker diarization - Updated for compatibility with newer SDK versions
            if config_options.get('speaker_diarization'):
                # Use speaker_count instead of speaker_labels for newer SDK versions
                config.speaker_count = 2  # Auto-detect number of speakers
            
            # Auto chapters
            if config_options.get('auto_chapters'):
                config.auto_chapters = True
            
            # Entity detection
            if config_options.get('entity_detection'):
                config.entity_detection = True
            
            # Content moderation
            if config_options.get('content_moderation'):
                config.content_safety = True
            
            # Format options
            if config_options.get('format_text'):
                config.punctuate = True
                config.format_text = True
        
        # Create transcriber and start transcription
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path, config=config)
        return transcript
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

def analyze_transcript_with_gpt(transcript_text, prompt_template=None, model="gpt-4o-search-preview", 
                        max_tokens=1500, temperature=0.7):
    """
    Send transcribed text to OpenAI for analysis.
    
    Args:
        transcript_text (str): The transcribed text to analyze
        prompt_template (str, optional): Custom prompt template to use
        model (str, optional): OpenAI model to use
        max_tokens (int, optional): Maximum number of tokens in the response
        temperature (float, optional): Temperature for response generation (0.0-2.0)
        
    Returns:
        dict: OpenAI response data
    """
    if not openai_client:
        raise ValueError("OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file.")
    
    # Add debug output to check transcript text
    print(f"TRANSCRIPT DEBUG - Received transcript of type: {type(transcript_text)}")
    print(f"TRANSCRIPT DEBUG - Received transcript of length: {len(str(transcript_text)) if transcript_text else 0}")
    print(f"TRANSCRIPT DEBUG - First 100 chars: {str(transcript_text)[:100] if transcript_text else 'EMPTY'}")
    print(f"MODEL DEBUG - Using model: {model} with max_tokens: {max_tokens}, temperature: {temperature}")
    
    # Validate transcript text
    if not transcript_text:
        print("TRANSCRIPT DEBUG - ERROR: Transcript text is None or empty")
        raise ValueError("No transcript text provided for analysis. Please check the transcription process.")
    
    if not isinstance(transcript_text, str):
        print(f"TRANSCRIPT DEBUG - ERROR: Transcript text is not a string, it's a {type(transcript_text)}")
        # Try to convert to string
        try:
            transcript_text = str(transcript_text)
            print(f"TRANSCRIPT DEBUG - Converted transcript to string, new length: {len(transcript_text)}")
        except Exception as e:
            print(f"TRANSCRIPT DEBUG - ERROR: Failed to convert transcript to string: {str(e)}")
            raise ValueError(f"Transcript text is not a string and couldn't be converted: {str(e)}")
    
    if len(transcript_text.strip()) == 0:
        print("TRANSCRIPT DEBUG - ERROR: Transcript text is just whitespace")
        raise ValueError("Transcript text is empty (contains only whitespace). Please check the transcription process.")
    
    # Use a default prompt template if none is provided
    if not prompt_template:
        prompt_template = "Please analyze the following transcript and provide key insights: {transcript}"
    
    # Debug check for {transcript} placeholder in prompt template
    if "{transcript}" not in prompt_template:
        print("PROMPT DEBUG - WARNING: Prompt template does not contain {transcript} placeholder!")
        # Append a default prompt to include the placeholder
        prompt_template += "\n\nHere is the transcript to analyze: {transcript}"
        print(f"PROMPT DEBUG - Updated prompt template to include placeholder: {prompt_template}")
    
    # Replace the placeholder with the actual transcript
    try:
        prompt = prompt_template.format(transcript=transcript_text)
    except Exception as e:
        print(f"PROMPT DEBUG - ERROR: Failed to format prompt template: {str(e)}")
        # Fallback to a simple format
        prompt = f"{prompt_template}\n\n{transcript_text}"
    
    # Enforce model-specific token limits
    model_specific_limits = {
        "gpt-4o": 16384,
        "gpt-4o-mini": 16384,
        "o1-mini-2024-09-12": 100000,
        "o3-mini-2025-01-31": 100000,
        "o1-preview-2024-09-12": 100000,
        "gpt-4o-search-preview": 32768,
        "gpt-4-turbo": 4096,
        "gpt-4-vision-preview": 4096,
        "gpt-4": 4096,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "claude-3-opus-20240229": 4096,
        "claude-3-sonnet-20240229": 4096,
        "claude-3-haiku-20240307": 4096
    }
    
    # Get the model limit or use a default of 4000
    model_limit = model_specific_limits.get(model, 4000)
    
    # Cap max_tokens to the model's limit
    if max_tokens > model_limit:
        print(f"MODEL DEBUG - Limiting max_tokens from {max_tokens} to {model_limit} for model {model}")
        max_tokens = model_limit
    
    try:
        # Check for models that don't support system role
        uses_limited_roles = any(model_id in model for model_id in [
            "o1-mini-2024-09-12", 
            "o3-mini-2025-01-31", 
            "o1-preview-2024-09-12"
        ])

        # Different API call for different models
        if uses_limited_roles:
            # These models don't support system role, only use user role
            # They also use max_completion_tokens instead of max_tokens
            # They don't support custom temperature values (only default of 1)
            print(f"MODEL DEBUG - Using limited roles configuration for {model} (without system role and temperature)")
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "You are an expert at analyzing audio transcripts. " + prompt}
                ],
                max_completion_tokens=max_tokens  # Using max_completion_tokens instead of max_tokens
                # Not including temperature parameter for these models as they only support the default value
            )
        elif "search" in model or "claude" in model:
            # Don't include temperature parameter for search models and Claude models
            print("MODEL DEBUG - Using search model configuration (without temperature parameter)")
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing audio transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
        else:
            # Include temperature for non-search models
            print("MODEL DEBUG - Using standard model configuration (with temperature parameter)")
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing audio transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        return {
            "analysis": response.choices[0].message.content,
            "model": model,
            "prompt": prompt
        }
    except Exception as e:
        print(f"GPT DEBUG - ERROR: Failed to analyze with GPT: {str(e)}")
        raise Exception(f"Analysis failed: {str(e)}")

def check_transcription_status(transcript_id):
    """
    Check the status of a transcription.
    
    Args:
        transcript_id (str): ID of the transcript
        
    Returns:
        str: Status of the transcription
    """
    transcriber = aai.Transcriber()
    try:
        status = transcriber.get_transcript(transcript_id).status
        return status
    except Exception as e:
        raise Exception(f"Status check failed: {str(e)}")

def poll_for_completion(transcript_id, polling_interval=5):
    """
    Poll for transcription completion.
    
    Args:
        transcript_id (str): ID of the transcript
        polling_interval (int, optional): Time between polling attempts
        
    Returns:
        aai.Transcript: Completed transcript
    """
    transcriber = aai.Transcriber()
    while True:
        try:
            transcript = transcriber.get_transcript(transcript_id)
            if transcript.status == 'completed':
                return transcript
            elif transcript.status == 'error':
                raise Exception(f"Transcription failed: {transcript.error}")
            time.sleep(polling_interval)
        except Exception as e:
            raise Exception(f"Polling failed: {str(e)}")

def save_transcript_to_file(transcript_text, output_path):
    """
    Save transcript to a file.
    
    Args:
        transcript_text (str): Text of the transcript
        output_path (str): Path to save the transcript
        
    Returns:
        bool: True if successful
    """
    try:
        with open(output_path, 'w') as f:
            f.write(transcript_text)
        return True
    except Exception as e:
        raise Exception(f"Failed to save transcript: {str(e)}")

def get_transcript_data(transcript):
    """
    Extract useful data from a transcript object.
    
    Args:
        transcript (aai.Transcript): Transcript object
        
    Returns:
        dict: Dictionary containing transcript data
    """
    data = {
        'text': transcript.text,
        'status': transcript.status,
        'id': transcript.id,
    }
    
    # Add speaker diarization data if available
    try:
        if hasattr(transcript, 'utterances') and transcript.utterances:
            data['utterances'] = [
                {
                    'speaker': u.speaker,
                    'text': u.text,
                    'start': u.start,
                    'end': u.end
                } for u in transcript.utterances
            ]
    except Exception:
        data['utterances'] = []
    
    # Add chapters if available
    try:
        if hasattr(transcript, 'chapters') and transcript.chapters:
            data['chapters'] = [
                {
                    'headline': c.headline,
                    'summary': c.summary,
                    'start': c.start,
                    'end': c.end
                } for c in transcript.chapters
            ]
    except Exception:
        data['chapters'] = []
    
    # Add entities if available
    try:
        if hasattr(transcript, 'entities') and transcript.entities:
            data['entities'] = [
                {
                    'text': e.text,
                    'entity_type': e.entity_type
                } for e in transcript.entities
            ]
    except Exception:
        data['entities'] = []
    
    return data 