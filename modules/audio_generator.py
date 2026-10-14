import edge_tts
import asyncio
import os
import subprocess

class AudioGenerator:
    def __init__(self, output_dir="output/audio"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # Voice options: en-US-ChristopherNeural, en-US-EricNeural, es-ES-AlvaroNeural, etc.
        # Voice options: en-US-ChristopherNeural, en-GB-RyanNeural (Natural/Documentary)
        self.voice = "en-GB-RyanNeural" 

    async def generate_audio(self, text, filename):
        """
        Generates TTS audio for the given text.
        """
        output_path = os.path.join(self.output_dir, filename)
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)
        return output_path

    async def generate_full_narration(self, script_scenes):
        """
        Generates audio for each scene.
        Returns a list of audio file paths corresponding to the scenes.
        """
        audio_files = []
        for i, scene in enumerate(script_scenes):
            filename = f"scene_{i}.mp3"
            text = scene.get('narration', '')
            if text:
                path = await self.generate_audio(text, filename)
                audio_files.append(path)
            else:
                audio_files.append(None)
        return audio_files

    def generate_ambience(self, output_filename="ambience.mp3", duration=60):
        """
        Generates a synthetic underwater/drone ambience using FFmpeg lavfi.
        """
        output_path = os.path.join(self.output_dir, output_filename)
        # If exists, return
        if os.path.exists(output_path):
            return output_path
            
        print(f"[AudioGenerator] Generating ambience: {output_filename}")
        # Brown noise + Lowpass = Underwater Rumble
        # anoisesrc needs recent ffmpeg. Fallback to sine if fails? No, let's assume valid ffmpeg.
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"anoisesrc=color=brown:d={duration}",
            "-af", "lowpass=f=200,volume=0.5",
            "-c:a", "libmp3lame",
            output_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path

    def generate_sfx_library(self):
        """
        Generates a set of synthetic SFX (Pop, Hit, Static) if they don't exist.
        Returns a dict of name -> path.
        """
        sfx_dir = os.path.join(self.output_dir, "sfx_gen")
        os.makedirs(sfx_dir, exist_ok=True)
        
        library = {}
        
        # 1. Pop (High sine blip)
        pop_path = os.path.join(sfx_dir, "pop.mp3")
        if not os.path.exists(pop_path):
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "sine=f=1000:d=0.1",
                "-af", "afade=t=out:st=0:d=0.1",
                "-c:a", "libmp3lame", pop_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        library['pop'] = pop_path
        
        # 2. Low Hit (Kick-like)
        hit_path = os.path.join(sfx_dir, "hit.mp3")
        if not os.path.exists(hit_path):
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "sine=f=60:d=0.3",
                "-af", "afade=t=out:st=0:d=0.3,volume=1.5",
                "-c:a", "libmp3lame", hit_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        library['hit'] = hit_path
        
        # 3. Static (White noise burst)
        static_path = os.path.join(sfx_dir, "static.mp3")
        if not os.path.exists(static_path):
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anoisesrc=color=white:d=0.2",
                "-af", "volume=0.3,afade=t=out:st=0:d=0.2",
                "-c:a", "libmp3lame", static_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        library['static'] = static_path
        
        return library
