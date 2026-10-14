import os
import subprocess
import textwrap
import re
import random

class VideoEditor:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def wrap_text(self, text, width=30):
        return textwrap.fill(text, width)

    def get_audio_duration(self, audio_path):
        """Returns the duration of an audio file in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe", 
                "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                audio_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"[VideoEditor] Error getting duration for {audio_path}: {e}")
            return 3.0 # Fallback/Safe default

    def create_intro_clip(self, audio_path, output_filename):
        """
        Creates the intro clip: "Did you know that?"
        Text centered, simple black background or maybe a dynamic color?
        Let's stick to black background for now, or maybe a stock image if available.
        For now: Black background with big text.
        """
        duration = 2.5 # approximate duration for "Did you know that?"
        
        # Create temp SRT for intro
        srt_path = os.path.join(self.output_dir, "intro.srt")
        self.create_srt_content("Did you know that?", duration, srt_path)
        srt_path_escaped = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
        
        # Style for Intro (Big, Centered)
        style = "Alignment=10,FontSize=30,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Fontname=Fredoka One"

        # Generate Clip
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-vf", f"subtitles=filename='{srt_path_escaped}':force_style='{style}'",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            os.path.join(self.output_dir, output_filename)
        ]
        # Add check=True to raise exception on failure
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Mix Intro Audio
        if audio_path and os.path.exists(audio_path):
            temp_intro = os.path.join(self.output_dir, "intro_with_audio.mp4")
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", os.path.join(self.output_dir, output_filename),
                "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", 
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest",
                temp_intro
            ]
            subprocess.run(cmd_mix, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return temp_intro
        
        return os.path.join(self.output_dir, output_filename)


    def create_srt_content(self, text, duration, filepath, audio_duration=None):
        """
        Creates a SRT file for the clip with 'Magnetic Captions'.
        Splits text into 1-3 word chunks.
        Centers text.
        Uses bright colors.
        """
        # pacing_duration is what we distribute the text over.
        # If audio_duration is provided, use that (so text ends when audio ends).
        # Otherwise use full clip duration.
        pacing_duration = audio_duration if audio_duration else duration
        
        # Split text into words
        # ... (rest of logic is same, just using pacing_duration)
        
        # BRAND STYLE: Word-by-word (Karaoke Style)
        # User said: "Aparezca palabra por palabra al ritmo de la voz."
        # We need strict 1-word chunks mostly, maybe grouping "a", "the" with next word.
        # BRAND STYLE V3: "BURST" Mode (Ráfagas)
        # User request: "En lugar de poner 'the' y luego 'tunicate', haz que las palabras aparezcan en ráfaga."
        # Logic: Group 2-3 words, or up to ~15 characters.
        words = text.split()
        chunks = []
        current_chunk = []
        current_len = 0
        
        for w in words:
            # Burst Logic:
            # If current chunk is empty, add word.
            # If adding word keeps length < 15 char AND chunk has < 3 words -> add.
            # Else -> push chunk, start new.
            if not current_chunk:
                current_chunk.append(w)
                current_len += len(w)
            elif current_len + len(w) + 1 < 20 and len(current_chunk) < 3:
                current_chunk.append(w)
                current_len += len(w) + 1
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [w]
                current_len = len(w)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        if not chunks:
             # Just in case regex fails or text is empty
            if text.strip():
                chunks = [text.strip()]
            else:
                return # Empty text
        
        # Calculate duration for each chunk
        total_chars = sum(len(c) for c in chunks)
        
        srt_content = ""
        current_time = 0.0
        
        # Colors (ASS Format: &HBBGGRR&)
        # Base: White (&HFFFFFF&)
        # Pop: Yellow (&H00FFFF&) - BGR Format (Blue=00, Green=FF, Red=FF)
        COLOR_YELLOW = "&H00FFFF&"
        COLOR_WHITE = "&HFFFFFF&"
        
        for i, chunk in enumerate(chunks):
            # ... (unchanged time logic) ...
            if total_chars > 0:
                p_duration = (len(chunk) / total_chars) * pacing_duration
            else:
                p_duration = pacing_duration / len(chunks)
            
            start_time = current_time
            end_time = current_time + p_duration
            
            # Helper to format time (unchanged)
            def format_time(t):
                hours = int(t // 3600)
                minutes = int((t % 3600) // 60)
                seconds = int(t % 60)
                milliseconds = int((t * 1000) % 1000)
                return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
            
            # Highlight Logic
            highlighted_chunk = ""
            chunk_words_split = chunk.split(" ")
            
            for w in chunk_words_split:
                clean_w = w.strip(".,!?'\"") 
                # Highlight if Uppercase
                if clean_w.isupper() and len(clean_w) > 1:
                     # Use HTML tags for SRT compatibility (FFmpeg supports this)
                     # Yellow: #FFFF00
                     colored_w = f'<font color="#FFFF00"><b>{w}</b></font>'
                     highlighted_chunk += colored_w + " "
                else:
                     highlighted_chunk += w + " "
            
            highlighted_chunk = highlighted_chunk.strip()

            srt_content += f"{i+1}\n{format_time(start_time)} --> {format_time(end_time)}\n{highlighted_chunk}\n\n"
            
            current_time = end_time

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
    def create_scene_clip(self, text, duration, output_filename, background_media=None):
        # ... (lines 153-227) ...
        # ...
        # User requested style: Magnetic Captions Reduced
        # Alignment=2 (Bottom Center with margin) to avoid blocking visuals?
        # User said: "Tercio central o inferior". Alignment=2 is Bottom Center.
        # FontSize: Reduced to 40 (was 70).
        # MarginV: 50 (to leave air)
        # Font: Montserrat Black / Arial Black (Impactful but clean)
        # Let's stick to Fredoka One or try Roboto if available? stick to generic compatible.
        
        srt_filename = output_filename.replace(".mp4", ".srt")
        srt_path = os.path.join(self.output_dir, srt_filename)
        self.create_srt_content(text, duration, srt_path)
        
        srt_path_escaped = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
        
        style = "Alignment=2,FontSize=40,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Fontname=Arial Must Be Bold,MarginV=150"
        
        # Append subtitles
        # ...

    def create_scene_clip(self, text, duration, output_filename, background_media=None, audio_duration=None):
        """
        Creates a video clip with text. 
        Background can be an Image or a Video.
        Forces 9:16 (1080x1920) for Shorts.
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        wrapped_text = self.wrap_text(text, width=60) 
        safe_text = wrapped_text.replace(":", "\\:").replace("'", "").replace("’", "")
        
        # Determine input type
        inputs = []
        is_video = False
        if background_media and os.path.exists(background_media):
            if background_media.endswith(".mp4"):
                is_video = True
                inputs = ["-stream_loop", "-1", "-i", background_media] # Loop video
            else:
                inputs = ["-loop", "1", "-i", background_media] # Loop image
        else:
             inputs = ["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}"]

        # Filter Chain:
        # If VIDEO: Scale to fill 1080x1920, Crop Center.
        # If IMAGE: Apply Ken Burns (Zoom In) effect.
        
        if is_video:
            filter_complex = (
                 "scale=1920:1920:force_original_aspect_ratio=increase," 
                 "crop=1080:1920,"                                      
                 "setsar=1"
            )
        else:
            # Ken Burns V2: Constant Slow Zoom (The "Creep")
            # User request: "Zoom constante y lento... acercamiento gradual"
            # We zoom IN from 1.0 to ~1.2 over the duration.
            # zoom+0.0005 per frame is very slow. 
            # 30fps * 5s = 150 frames. 0.001 * 150 = 0.15 increase.
            # Let's use 0.0015 for a noticeable but smooth creep.
            
            frames = int(duration * 30) # 30fps
            
            # Simple Center Zoom IN
            # z='min(zoom+0.0015,1.5)'
            # x='iw/2-(iw/zoom/2)' (Center X)
            # y='ih/2-(ih/zoom/2)' (Center Y)
            # s=1080x1920
            
            filter_complex = (
                f"scale=-1:5760," 
                f"zoompan=z='min(zoom+0.0015,1.5)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
            )

        # Create temp SRT file for this clip
        srt_filename = output_filename.replace(".mp4", ".srt")
        srt_path = os.path.join(self.output_dir, srt_filename)
        self.create_srt_content(text, duration, srt_path, audio_duration=audio_duration)
        
        # Escape path for FFmpeg filter
        srt_path_escaped = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")

        # User requested style: Magnetic Captions Reduced (Brand Style V6 - Corrected Yellow Highlight)
        # Alignment=2 (Bottom Center)
        # FontSize: 20
        # MarginV: 100
        # Font: Arial Black
        # PrimaryColour: &H00FFFFFF (White) -> Base text is White.
        style = "Alignment=2,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=2,Fontname=Arial Black,MarginV=100"
        
        # Append subtitles
        filter_complex += f",subtitles=filename='{srt_path_escaped}':force_style='{style}'"



        cmd = [
            "ffmpeg", "-y",
        ] + inputs + [
            "-t", str(duration),
            "-vf", filter_complex,
            # High Quality Encoding Settings
            "-c:v", "libx264", 
            "-pix_fmt", "yuv420p", 
            "-r", "30",
            "-preset", "slow", 
            "-crf", "16", 
            output_path
        ]
        
        # print(f"[FFmpeg] Rendering scene: {text[:15]}... (Media: {background_media})")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path

    # ... (rest of methods) ...

    # ... (rest of methods) ...

    def assemble_final_video(self, scenes, audio_files, media_files=None, final_filename="final_video.mp4", intro_audio_path=None, ambience_path=None, sfx_library=None):
        clips = []
        if not media_files:
            media_files = [None] * len(scenes)

        print(f"[VideoEditor] Assembling {len(scenes)} scenes (Viral Mode: No Intro, Swoosh SFX)...")
        
        # Load Transition SFX Library
        sfx_dir = "assets/sfx"
        transition_files = []
        if os.path.exists(sfx_dir):
            transition_files = [f for f in os.listdir(sfx_dir) if f.lower().endswith((".mp3", ".wav"))]
        
        # Fallback if specific file missing but logic needs implies "Swoosh.mp3" was default
        # We will pick randomly later.
        has_sfx = len(transition_files) > 0
        
        for i, (scene, audio_path, media_path) in enumerate(zip(scenes, audio_files, media_files)):
             # ... (logic to create temp_clip) ...
            duration = scene['duration'] 
            
            # Get exact audio duration for subtitle sync
            audio_dur = 0
            scene_narration = scene.get('narration', '')
            if audio_path and os.path.exists(audio_path):
                audio_dur = self.get_audio_duration(audio_path)
            
            # DYNAMIC PACING: User wants "no stops" if phrase continues.
            # Smart Padding Logic
            padding = 0.5 # Default pause for end of sentence
            text = scene_narration.strip()
            if text and not text.endswith(('.', '!', '?')):
                # Split sentence -> Tight cut to next scene
                padding = 0.1 
            
            if audio_dur > 0:
                # If flow is tight (0.1), we might want to relax the 2.0 min limit? 
                # If audio is 1.5s + 0.1 = 1.6s. 2.0s min would add 0.4s silence.
                # Let's reduce min duration for split sentences to keep flow.
                min_dur = 2.0 if padding > 0.3 else 1.0
                duration = max(audio_dur + padding, min_dur)
            else:
                duration = max(scene['duration'], 3.0) # Fallback if no audio
            
            # Pass audio_dur to create_scene_clip for correct subtitle pacing (Subtitle ends at audio_dur)
            visual_clip = self.create_scene_clip(scene_narration, duration, f"scene_{i}.mp4", media_path, audio_duration=audio_dur)
            temp_clip = os.path.join(self.output_dir, f"clip_{i}.mp4")
            
            # Mix voice with optional swosh AND micro-sfx
            cmd = None
            if audio_path:
                inputs = ["-i", visual_clip, "-i", audio_path] # 0: Video, 1: Voice
                filter_str = "[1:a]volume=1.0[voice]"
                map_a = "[outa]"
                current_input_idx = 2
                
                mix_inputs = ["[voice]"]
                
                # SMART SWOOSH LOGIC
                # User Request: Don't play swoosh if sentence continues from previous scene.
                play_swoosh = True
                if i > 0:
                     prev_text = scenes[i-1].get('narration', '').strip()
                     # If prev text exists and DOES NOT end with . ! ?, it's likely a split sentence.
                     if prev_text and not prev_text.endswith(('.', '!', '?')):
                         play_swoosh = False

                # 1. Add Swoosh (Transition) - Low Volume
                if has_sfx and play_swoosh:
                    # Pick random transition SFX for variety
                    sfx_filename = random.choice(transition_files)
                    sfx_path = os.path.join(sfx_dir, sfx_filename)
                    
                    inputs += ["-i", sfx_path] 
                    # Delay Swoosh to near end.
                    delay_ms = int(max(0, (duration - 0.5) * 1000)) 
                    # Volume reduced to 0.04 (Even quieter)
                    filter_str += f";[{current_input_idx}:a]adelay={delay_ms}|{delay_ms},volume=0.04[sfx]"
                    mix_inputs.append("[sfx]")
                    current_input_idx += 1
                
                # 2. Add Random Micro-SFX (Texture)
                # 50% chance to add a random tick/pop/static
                if sfx_library and random.random() < 0.6:
                    # Pick random SFX
                    sfx_key = random.choice(list(sfx_library.keys()))
                    micro_sfx_path = sfx_library[sfx_key]
                    
                    if os.path.exists(micro_sfx_path):
                        inputs += ["-i", micro_sfx_path]
                        # Random delay (start or middle)
                        micro_delay = int(random.uniform(0, duration - 1.0) * 1000)
                        # Very low volume for texture
                        filter_str += f";[{current_input_idx}:a]adelay={micro_delay}|{micro_delay},volume=0.15[micro]"
                        mix_inputs.append("[micro]")
                        current_input_idx += 1
                        print(f"   + Added Micro-SFX: {sfx_key} at {micro_delay}ms")

                # Mix all audio inputs
                if len(mix_inputs) > 1:
                    filter_str += f";{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=longest[outa]"
                else:
                    filter_str += ";[voice]anull[outa]" # No SFX, just mapped voice
                
                cmd = [
                    "ffmpeg", "-y",
                ] + inputs + [
                    "-filter_complex", filter_str,
                    "-map", "0:v:0", "-map", map_a,
                    # trim to video duration
                    "-t", str(duration),
                    "-c:v", "copy", "-c:a", "aac", 
                    temp_clip
                ]
            else:
                temp_clip = visual_clip 
            
            # Check=True to ensure if assembly fails we fail the pipeline
            if cmd:
                 subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            clips.append(temp_clip)

        # Concat Visuals
        list_file_path = os.path.join(self.output_dir, "clips.txt")
        with open(list_file_path, "w") as f:
            for clip in clips:
                clean_path = os.path.abspath(clip).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        temp_narration_video = os.path.join(self.output_dir, "temp_narration.mp4")
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", list_file_path,
            "-c", "copy",
            temp_narration_video
        ]
        subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 3. Add Background Music & Ambience
        music_files = [f for f in os.listdir("assets/music") if f.lower().endswith((".mp3", ".wav"))]
        
        final_output = os.path.join(self.output_dir, final_filename)

        # Determine Music
        music_path = None
        if music_files:
            music_file = random.choice(music_files)
            music_path = os.path.join("assets/music", music_file)
            print(f"[VideoEditor] Adding background music: {music_path}")
        
        # Build Filter Complex for Audio Mixing
        # Inputs: 
        # 0: Video (with Voice+SFX)
        # 1: Music (Optional)
        # 2: Ambience (Optional)
        
        inputs = ["-i", temp_narration_video]
        input_count = 1
        filter_parts = ""
        mix_inputs = ["[0:a]"]
        
        # Prepare Music Input
        if music_path:
            inputs += ["-stream_loop", "-1", "-i", music_path]
            # Volume 0.05 for music (Very Low as requested)
            filter_parts += f"[{input_count}:a]volume=0.05[music];"
            mix_inputs.append("[music]")
            input_count += 1
        
        # Prepare Ambience Input
        if ambience_path and os.path.exists(ambience_path):
            print(f"[VideoEditor] Adding ambience: {ambience_path}")
            inputs += ["-stream_loop", "-1", "-i", ambience_path]
            # Volume 0.5 for Ambience (Rumble) - Keep as is, it's subtle noise.
            filter_parts += f"[{input_count}:a]volume=0.5[ambience];"
            mix_inputs.append("[ambience]")
            input_count += 1
            
        if len(mix_inputs) > 1:
            # amix command
            # inputs=N:duration=first (video duration)
            filter_parts += "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=first[out]"
            
            mix_cmd = [
                "ffmpeg", "-y",
            ] + inputs + [
                "-filter_complex", filter_parts,
                "-map", "0:v:0", "-map", "[out]",
                "-c:v", "copy", 
                "-c:a", "aac",
                final_output
            ]
            subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        else:
             # Just rename
             os.rename(temp_narration_video, final_output)

        return final_output
