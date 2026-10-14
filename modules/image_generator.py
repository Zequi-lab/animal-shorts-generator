import os
import urllib.request
import urllib.parse
import time

class ImageGenerator:
    def __init__(self, output_dir="output/images"):
        self.output_dir = output_dir
        self.ua_header = {'User-Agent': 'Mozilla/5.0'}
        os.makedirs(output_dir, exist_ok=True)

    def _download_image(self, url, output_path):
        """Helper to download image from URL."""
        try:
            req = urllib.request.Request(url, headers=self.ua_header)
            with urllib.request.urlopen(req) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            return True
        except Exception as e:
            print(f"[ImageGen] Download Error: {e}")
            return False

    def generate_image(self, prompt, filename):
        """Generates an image. Tries Pollinations, falls back to Picsum."""
        output_path = os.path.join(self.output_dir, filename)

        # 1. Try Pollinations.ai
        full_prompt = f"{prompt}, documentary photography, natural light, biologically accurate, 8k"
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux"

        if self._download_image(url, output_path):
            return output_path

        # 2. Fallback to Picsum (Random Nature Image)
        print(f"[ImageGen] Falling back to Picsum for: {filename}...")
        picsum_url = f"https://picsum.photos/1080/1920?random={int(time.time())}"
        if self._download_image(picsum_url, output_path):
            return output_path

        return None

    def generate_scene_images(self, scenes, topic=None):
        """Generates images for all scenes."""
        image_paths = []
        for i, scene in enumerate(scenes):
            filename = f"scene_{i}.jpg"
            base_prompt = scene.get('visual_description', "Wildlife nature shot")

            # Prepend topic for context (ensures species name in prompt)
            prompt = f"{topic}, {base_prompt}" if topic else base_prompt

            # VIRAL HOOK: Scene 0 gets extreme close-up treatment
            if i == 0:
                prompt += ", extreme close up of eyes, macro photography, award winning wildlife photography, national geographic style, highly detailed, 8k"

            path = self.generate_image(prompt, filename)
            image_paths.append(path)
            # Light polite delay (reduced from 1s to avoid bottleneck)
            if i < len(scenes) - 1:
                time.sleep(0.3)
        return image_paths
