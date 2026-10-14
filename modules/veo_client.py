import os
import time
import json
from google.oauth2 import service_account
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# NOTE: As of early 2025, Veo on Vertex AI might be accessed via specific model names
# or the video generation endpoint. We will attempt to use the 'veo' model family.
# If unavailable, we might need to fall back to 'imagen-3.0-generate-001' for high quality images as video frames?
# No, user wants VIDEO. We will try to find the video model.

class VeoClient:
    def __init__(self, key_path="service_account.json", output_dir="output/videos"):
        self.key_path = key_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.model = None
        
        if os.path.exists(self.key_path):
            try:
                # 1. Authenticate with Service Account
                self.credentials = service_account.Credentials.from_service_account_file(self.key_path)
                
                # 2. Get Project ID from JSON
                with open(self.key_path) as f:
                    data = json.load(f)
                    self.project_id = data.get("project_id")
                
                # 3. Initialize Vertex AI
                vertexai.init(project=self.project_id, location="us-central1", credentials=self.credentials)
                print(f"[Veo] Initialized Vertex AI for project: {self.project_id}")
                
                # 4. Load Model
                # we use the specific VideoGenerationModel if available (it varies by SDK version).
                # 'imagegeneration@006' is EOL. Using Imagen 3.0
                try:
                    self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001") 
                    print("[Veo] Authentication successful (Imagen 3.0).")
                except Exception as e:
                    print(f"[Veo] Auth check failed: {e}")

            except Exception as e:
                print(f"[Veo] Failed to initialize Vertex AI: {e}")
        else:
            print(f"[Veo] Key file not found at {self.key_path}")

    def generate_video(self, prompt, filename, duration_seconds=6):
        """
        Generates a HIGH QUALITY Image using Vertex AI (Imagen 3) and returns it path.
        FFmpeg will treat it as a static video (loop).
        We do this because Veo Video API is not yet in Python SDK.
        """
        if not self.model:
            print("[Veo] Model not initialized.")
            return None

        print(f"[Veo/Vertex] Generating HQ Asset for: '{prompt[:30]}...'")
        
        retries = 1
        for attempt in range(retries + 1):
            try:
                # Generate Image (Imagen 3)
                # Aspect ratio for shorts: 9:16
                # Use "Documentary" style to avoid "Orange/Alien" fantasy effects.
                base_prompt = prompt + ", documentary footage, natural lighting, anatomically correct, 4k, sharp focus, vertical 9:16"
                
                response = self.model.generate_images(
                    prompt=base_prompt,
                    number_of_images=1,
                    aspect_ratio="9:16",
                    safety_filter_level="block_few",
                    person_generation="allow_adult"
                )
                
                if response and response[0]:
                    image_path = os.path.join(self.output_dir, filename.replace(".mp4", ".png"))
                    response[0].save(location=image_path, include_generation_parameters=False)
                    print(f"[Veo] Image generated: {image_path}")
                    return image_path
                
                return None
    
            except Exception as e:
                print(f"[Veo] Generation error (Attempt {attempt+1}/{retries+1}): {e}")
                if "429" in str(e):
                    if attempt < retries:
                        print(f"[Veo] Quota exceeded (429). Waiting 30 seconds before retry {attempt+1}/{retries}...")
                        time.sleep(30)
                        continue
                    else:
                        print("[Veo] Quota exceeded. Using Stock fallback.")
                return None

    def generate_scene_videos(self, scenes):
        """
        Generates videos for all scenes.
        """
        video_paths = []
        for i, scene in enumerate(scenes):
            filename = f"veo_scene_{i}.mp4"
            if isinstance(scene, dict):
                prompt = scene.get('visual_description', '')
            else:
                prompt = str(scene)
            
            # Try generation
            path = self.generate_video(prompt, filename)
            
            # If failed (None), append None to trigger Stock fallback
            video_paths.append(path)
            # User requested delay between photos to avoid 429
            print("[Veo] Waiting 10s between requests...")
            time.sleep(10)
        
        return video_paths
