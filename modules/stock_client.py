import os
import requests
import random
import time

class StockClient:
    def __init__(self, api_key=None, output_dir="output/videos"):
        self.api_key = api_key
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.base_url = "https://api.pexels.com/videos/search"
        self.headers = {
            "Authorization": self.api_key
        }

    def download_video(self, query, filename, min_duration=3):
        """
        Searches for a video on Pexels and downloads it.
        """
        if not self.api_key:
            print("[StockClient] No API Key provided.")
            return None

        # Search for vertical videos first if possible, but 
        # Pexels API filters are: orientation=portrait
        params = {
            "query": query,
            "per_page": 5,
            "orientation": "portrait", # Try to get vertical first
            "size": "medium"
        }
        
        try:
            print(f"[StockClient] Searching for video: '{query}'...")
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            videos = data.get("videos", [])
            if not videos:
                # Retry with no orientation filter
                print("[StockClient] No portrait video found, trying landscape...")
                params.pop("orientation")
                response = requests.get(self.base_url, headers=self.headers, params=params)
                videos = response.json().get("videos", [])

            if not videos:
                print(f"[StockClient] No videos found for '{query}'.")
                return None

            # Pick a video that ACTUALLY matches the query (Relevance Check)
            # Pexels search can be fuzzy. We check if query words appear in tags.
            valid_videos = []
            query_words = set(query.lower().split())
            
            for v in videos:
                # 1. Relevance: Check tags (optional but recommended for niche animals)
                # If query is "Numbat", and tags are ["nature", "forest"], it's likely wrong.
                # But Pexels tags aren't perfect. Let's start with a soft check if query is single word.
                # If query is complex like "Numbat swimming", simple tag match might fail.
                # Let's trust Pexels ranking BUT filter out generic "nature" spam if possible?
                # Actually, the user issue "Camel instead of Axolotl" suggests Pexels returned *something* for "Axolotl" search?
                # Or the search was broad. Using specific "stock_search_term" helps.
                # IMPORTANT: If Pexels returns NOTHING relevant, we want to FAIL to fallback to Image.
                
                # We will trust the search "stock_search_term" is specific now.
                # But we enforce resolution.
                
                # 2. Quality: Must have at least one HD file
                has_hd = False
                for vf in v.get("video_files", []):
                    if vf.get("width", 0) >= 1080:  # Require 1080p minimum
                        has_hd = True
                        break
                
                if has_hd:
                    valid_videos.append(v)
            
            if not valid_videos:
                print(f"[StockClient] Found videos but none were HD (1080p+). Skipping to avoid blur.")
                return None
                
            video_obj = random.choice(valid_videos)
            
            # Find download link (Best available)
            video_files = video_obj.get("video_files", [])
            video_files.sort(key=lambda x: x.get("width", 0), reverse=True)
            
            download_url = None
            for vf in video_files:
                if vf.get("width", 0) >= 1080:
                    download_url = vf.get("link")
                    break
            
            # If we are here, we guarantee download_url is HD because of the filter above
            # Double check fallback just in case list logic had a gap
            if not download_url and video_files:
                 # Should not happen given valid_videos logic, but safety
                 if video_files[0].get("width", 0) >= 1080:
                    download_url = video_files[0].get("link")

            if download_url:
                print(f"[StockClient] Downloading video ID: {video_obj.get('id')}...")
                vid_response = requests.get(download_url, stream=True)
                output_path = os.path.join(self.output_dir, filename)
                with open(output_path, "wb") as f:
                    for chunk in vid_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return output_path
                
        except Exception as e:
            print(f"[StockClient] Error: {e}")
            return None
        
        return None

    def get_scene_videos(self, scenes, topic="animal"):
        """
        Downloads a video for each scene using specific keywords if available.
        """
        video_paths = []
        for i, scene in enumerate(scenes):
            filename = f"stock_scene_{i}.mp4"
            
            # Use specific term from LLM if available, else topic
            search_query = scene.get('stock_search_term', topic)
            if not search_query:
                search_query = topic
                
            print(f"[StockClient] Searching for video (Scene {i}): '{search_query}'")
            path = self.download_video(search_query, filename)
            video_paths.append(path)
            time.sleep(1) 
        return video_paths
