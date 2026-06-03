import edge_tts
import asyncio
import os
import tempfile
import base64

async def play_speech_directly(text):
    """
    Generate speech and return audio data as base64 string.
    
    Args:
        text (str): English text to convert to speech
    
    Returns:
        dict: Contains 'audio_data' (base64-encoded MP3) and 'error' (if any)
    """
    try:
        voice = "en-US-JennyNeural"
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        # Generate and save to temp file
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp_path)

        # Read the audio file as binary and encode to base64
        print("Converting Audio")
        with open(tmp_path, 'rb') as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        print("Converting Complete")

        # Clean up
        os.unlink(tmp_path)

        return {"audio_data": audio_data, "error": None}

    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {"audio_data": None, "error": f"Error generating speech: {str(e)}"}

async def main():
    print("Edge TTS Audio Bot")
    print("----------------------------------")
    
    while True:
        print("\nOptions:")
        print("1. Speak English text")
        print("2. Exit")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == '1':
            text = input("Enter English text to speak: ")
            await play_speech_directly(text)
                
        elif choice == '2':
            print("Exiting the audio bot...")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())