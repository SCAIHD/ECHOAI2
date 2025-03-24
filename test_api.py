import os
import assemblyai as aai
from dotenv import load_dotenv

def test_api_key():
    """Test if the API key is valid by making a simple request."""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        print("❌ No API key found in .env file")
        return False
    
    print(f"🔑 Using API key: {api_key}")
    
    # Configure the API key
    aai.settings.api_key = api_key
    
    try:
        # Try to create a transcriber object
        transcriber = aai.Transcriber()
        print(f"✅ Created transcriber object")
        
        # Print the API key being used
        print(f"API key being used: {aai.settings.api_key}")
        
        return True
    except Exception as e:
        print(f"❌ API key validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_key() 