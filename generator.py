import os
import json
import asyncio
import shutil
import sys
from datetime import datetime, timedelta

from modules.llm_utils import LLMGenerator
from modules.veo_client import VeoClient
from modules.history_manager import HistoryManager
from modules.video_editor import VideoEditor
from modules.youtube_uploader import YouTubeUploader
from modules.audio_generator import AudioGenerator
from modules.image_generator import ImageGenerator
from modules.stock_client import StockClient

def clean_output_dir(output_dir="output"):
    """Cleans the output directory to prevent stale files from being used."""
    if os.path.exists(output_dir):
        print(f"[Generator] Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

def load_env(env_file=".env"):
    """Simple .env loader."""
    if not os.path.exists(env_file):
        return
    with open(env_file, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

def sanitize_topic(topic):
    """Sanitizes and normalizes topic string from LLM responses."""
    topic = str(topic).strip(' "\'{}\n\t')

    # If LLM returned JSON string
    if topic.startswith("{") and "}" in topic:
        try:
            data = json.loads(topic)
            topic = data.get("animal") or data.get("name") or data.get("topic") or list(data.values())[0]
            topic = str(topic).strip(' "\'{}\n\t')
        except (json.JSONDecodeError, (IndexError, AttributeError)):
            pass

    # Cleanup common prefixes (case insensitive)
    topic_lower = topic.lower()
    if topic_lower.startswith("name:"):
        topic = topic[5:].strip()
    elif topic_lower.startswith("animal:"):
        topic = topic[7:].strip()

    if topic.lower().endswith(":null"):
        topic = topic[:-5].strip()

    return topic

async def run_pipeline(topic=None):
    load_env()
    
    # 0. Clean previous run data
    clean_output_dir("output")
    
    # Init modules
    llm = LLMGenerator(
        api_key=os.getenv("LLM_API_KEY"),
        provider=os.getenv("LLM_PROVIDER", "ollama"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    veo = VeoClient(key_path="service_account.json")
    history = HistoryManager()
    editor = VideoEditor()
    uploader = YouTubeUploader()
    audio_gen = AudioGenerator()
    image_gen = ImageGenerator()
    stock_client = StockClient(api_key=os.getenv("PEXELS_API_KEY"))

    # 1. Topic Selection
    if not topic:
        print("\n--- AUTO MODE: Discovering new topic... ---")
        existing_topics = [item['topic'] for item in history.history]
        topic = await llm.suggest_topic(existing_topics)
        topic = sanitize_topic(topic)
        print(f"Sanitized Topic: '{topic}'")
    
    print(f"\n>>> PROCESSING TOPIC: {topic} <<<")

    # 2. Uniqueness Check
    if not history.is_unique(topic):
        print(f"Skipping duplicate topic: {topic}")
        return

    # 3. Generate Script
    print("Generating script...")
    script_data = await llm.generate_script(topic)
    
    # 4. Generate Media (Veo > Stock > Image)
    print("Acquiring Media...")
    media_files = []
    
    # Try Veo First (Vertex AI)
    if os.path.exists("service_account.json"):
        print("Attempting Veo Video Generation (Vertex AI)...")
        # Note: VeoClient currently strictly warns about API availability.
        media_files = veo.generate_scene_videos(script_data['scenes'])
        # Clean None values
        media_files = [f for f in media_files if f]
        
        if not media_files:
            print("[Veo] Generation failed or returned empty. Falling back to Stock Video...")
        
    if not media_files and os.getenv("PEXELS_API_KEY"):
         print("Searching Pexels for stock video...")
         media_files = stock_client.get_scene_videos(script_data['scenes'], topic=topic)
    
    # Check if we have valid videos, if not, generate images
    # We check per scene? For simplicity, if Pexels fails completely (None), we do full fallback.
    # Currently get_scene_videos returns list with None if failed individual scenes.
    
    final_media_files = []
    if media_files:
        for i, vid in enumerate(media_files):
            if vid and os.path.exists(vid):
                final_media_files.append(vid)
            else:
                # Fallback to image for this scene
                print(f"Fallback to Image for scene {i}...")
                
                # Contextualize Prompt
                visual_context = f"{topic}"
                if "scientific_name" in script_data:
                    visual_context += f" ({script_data['scientific_name']})"
                
                full_prompt = f"{visual_context}, {script_data['scenes'][i]['visual_description']}"
                img = image_gen.generate_image(full_prompt, f"fallback_{i}.jpg")
                final_media_files.append(img)
    else:
        # Full fallback if no key
        print("No Pexels Key or search failed. Generating AI Images...")
        
        # Pass Topic + Scientific Name Context
        visual_context = f"{topic}"
        if "scientific_name" in script_data:
             visual_context += f" ({script_data['scientific_name']})"
             
        final_media_files = image_gen.generate_scene_images(script_data['scenes'], topic=visual_context)
    
    # 5. Generate Audio (Edge TTS)
    print("Generating REAL Audio (TTS)...")
    audio_files = await audio_gen.generate_full_narration(script_data['scenes'])
    
    # Generate Intro Audio
    intro_audio_path = await audio_gen.generate_audio("Did you know that?", "intro_audio.mp3")

    # Generate Ambience (Viral Enhancement)
    print("Generating Ambience (Underwater/Drone)...")
    ambience_path = audio_gen.generate_ambience("ambience_drone.mp3")
    
    # Generate Micro-SFX Library
    sfx_library = audio_gen.generate_sfx_library()

    # 6. Assembly (Visuals + Audio)
    print("Rendering Video...")
    final_video = editor.assemble_final_video(
        script_data['scenes'], 
        audio_files, 
        final_media_files, 
        intro_audio_path=intro_audio_path, 
        ambience_path=ambience_path,
        sfx_library=sfx_library
    )
    
    # 7. Upload
    sanitized_topic = topic.replace(" ", "_").replace(":", "").replace("'", "")

    print("Uploading to YouTube...")
    video_id = None
    
    # Use generated description or fallback
    video_desc = script_data.get('description', "Generated by Automated Animal Shorts Bot #shorts #animals")
    
    try:
        video_id = uploader.upload_video(
            final_video, 
            script_data['title'], 
            video_desc, 
            ["shorts", "animals", topic]
        )
        print(f"\n[SUCCESS] Video '{topic}' deployed! ID: {video_id}")
    except Exception as e:
        print(f"\n[ERROR] YouTube Upload Failed (Quota or Error): {e}")
        video_id = "UPLOAD_FAILED"

    # 8. Save History
    output_data = {
        "metadata": {
            "title": script_data['title'],
            "topic": topic,
            "generated_at": history.add_entry(topic, video_id) 
        },
        "script": script_data,
        "veo_prompts": [], # Veo prompts are not stored in this logic currently
        "video_id": video_id
    }
    
    # Save JSON log
    with open(f"examples/{sanitized_topic}_data.json", "w", encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print("\n[CLEANUP] Borrando archivos temporales (videos/audios) para liberar memoria...")
    clean_output_dir("output")
    return True

async def main_loop():
    print("--- ANIMAL SHORTS AUTOMATION STARTED ---")
    print("Press Ctrl+C to stop.")

    # Schedule: 02:00, 10:00, 14:00, 17:00, 20:00, 23:00 (pre-sorted)
    TARGET_HOURS = [2, 10, 14, 17, 20, 23]

    while True:
        try:
            # 1. Run Pipeline
            await run_pipeline()

            # 2. Calculate Next Run Time
            now = datetime.now()
            next_run = None

            # Find next slot today
            for h in TARGET_HOURS:
                target = now.replace(hour=h, minute=0, second=0, microsecond=0)
                if target > now:
                    next_run = target
                    break

            # If no slot left today, pick earliest slot tomorrow
            if not next_run:
                next_run = now.replace(day=now.day, hour=TARGET_HOURS[0], minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            
            print(f"\n[SCHEDULER] Job complete. Next video scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"[SCHEDULER] Sleeping for {int(wait_seconds)} seconds...")
            
            await asyncio.sleep(wait_seconds) 
            
        except KeyboardInterrupt:
            print("Stopping automation.")
            break
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            print("Retrying in 60 seconds (Error Recovery)...")
            await asyncio.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        asyncio.run(run_pipeline("Blue Ringed Octopus")) # Manual single run test
    else:
        asyncio.run(main_loop())
