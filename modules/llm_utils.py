import json
import urllib.request
import urllib.error
import asyncio

class LLMGenerator:
    def __init__(self, api_key=None, provider="ollama", model="llama3", base_url="http://localhost:11434"):
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.base_url = base_url

    def _call_ollama(self, prompt, system_prompt, json_mode=True):
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        
        if json_mode:
            payload["format"] = "json"
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except urllib.error.URLError as e:
            print(f"[LLM Error] Could not connect to Ollama at {self.base_url}: {e}")
            return None

    def generate_script(self, topic):
        """
        Generates a script for a YouTube Short based on the topic using Ollama.
        """
        print(f"[LLM] Generating script for '{topic}' using {self.model}...")
        
        # ... (System Prompt) ...
        # We need to construct the system_instruction again or just reference existing?
        # The replace_file_content replaces the BLOCK.
        # I should be careful not to delete the huge system prompt.
        # Wait, I can just update the definition line of _call_ollama and the payload part.
        # But this tool requires contiguous block replacement.
        # I'll update _call_ollama first. Then suggest_topic.
        # Actually I can do it in one go if I include the whole file or just the relevant chunks.
        # But they are far apart? No, lines 13-32 and 128-141.
        # The tool documentation says: "To edit multiple, non-adjacent lines... make a single call to multi_replace_file_content".
        # I should use multi_replace_file_content.
        pass 

    # RETHINKING: I will use multi_replace_file_content.
    pass



    async def generate_script(self, topic):
        """
        Generates a script for a YouTube Short based on the topic using Ollama.
        """
        print(f"[LLM] Generating script for '{topic}' using {self.model}...")

        system_instruction = """
        You are a master viral content creator for YouTube Shorts (TikTok style). 
        You specialize in "Terror/Mystery" biology.
        
        CRITICAL GOAL: The Visuals MUST match the Narration EXACTLY. 
        If you talk about Australia, show a MAP of Australia. 
        If you talk about a fossil, show a SCIENTIFIC ILLUSTRATION. 
        Do NOT ask for generic animal photos if the subject is abstract or specific.

        RULES:
        RULES:
        1. **HOOK (NARRATION)**: 
           - **NEVER** start with "Meet the...", "This is...", or "Here we have...". 
           - **MUST** start with a SHOCKING statement or QUESTION.
           - Example: "If you see this animal, RUN." or "This creature has a secret weapon."
        2. **VISUALS**: 
           - **SCENE 1 RULE**: The first visual MUST be an "Extreme Close-up of Face", "Hyper-realistic", "Looking at camera".
           - Use styles: "Real Photo", "Scientific Illustration", "3D Render", "Animated Map".
           - **CRITICAL: DISAMBIGUATE**: If the animal has a misleading name (e.g., "Sea Pig", "Spider Crab"), **YOU MUST** add context or scientific name.
           - BAD: "Sea Pig" (Results in farm pigs).
           - GOOD: "Scotoplanes deep sea creature underwater".
           - **ALWAYS** include "animal", "creature", or habitat ("underwater", "jungle") in the search term.
           - **NO FANTASY**: Avoid "glowing eyes" or "alien lights" unless real (bioluminescence).
        3. **NARRATION (HIGH RETENTION)**: 
           - **SECOND PERSON**: Use "YOU" constantly. "Your nightmare", "If you touch it".
           - **NO WIKIPEDIA**: Do NOT say "It lives in...". Say "You'll find it hiding in...".
           - **FOCUS**: Danger, Superpowers, Weirdness.
           - **MINI-CLIFFHANGERS**: End sentences in a way that forces the viewer to watch the next scene.
           - Total 130 words.
        4. **INTERACTIVE CTA**: You MUST end with a specific question to provoke comments.
           - Example: "Would you dare to hold this in your hand? Tell me in the comments!"
           - **CRITICAL VISUAL RULE**: For this final scene, the visual MUST be the ANIMAL (e.g. looking at camera). 
        5. **KEYWORD HIGHLIGHTING**: Write KEYWORDS in UPPERCASE for the subtitles to highlight them.
        6. **LENGTH**: 30-45 seconds. ~150 words.
        7. **STRUCTURE (CRITICAL)**:
           - **TOTAL SECCENES**: 10-15 SCENES.
           - **MAX 3 SECONDS PER SCENE**.
           - **EVERY 2-3 SECONDS THE VISUAL MUST CHANGE.**
        
        Output JSON:
        {
            "title": "String (CLICKBAIT: 'The Nightmare of...', 'You won't believe...')",
            "topic": "String",
            "scientific_name": "String (Latin Name, e.g. Cryptoprocta ferox)",
            "description": "String (First line hook + 3 viral hashtags. E.g. 'This is why you should never touch a... #shorts #nature')",
            "scenes": [
                {
                    "start_time": int,
                    "duration": int,
                    "narration": "String (Max 5-8 words...)",
                    "visual_description": "String (STYLE: [Scientific Illustration/Photo]. SUBJECT: {scientific_name} doing X...)",
                    "stock_search_term": "String"
                }
            ]
        }
        """

        user_prompt = f"Create a script for a YouTube Short about '{topic}'. Focus on 'unknown facts' or 'curiosities'. Hook the viewer immediately."

        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                print(f"[LLM] Generating script for '{topic}' using {self.model}... (Attempt {attempt+1}/{MAX_RETRIES})")
                
                # Call Ollama
                response_text = await asyncio.to_thread(self._call_ollama, user_prompt, system_instruction, json_mode=True)
                
                if not response_text:
                     print(f"[LLM] Failed to get response (Attempt {attempt+1}).")
                     continue

                # Clean up potential markdown code blocks
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                script_json = json.loads(cleaned_text)
                
                # Fail-safe: Ensure title exists
                if "title" not in script_json:
                    script_json["title"] = f"Curiosidades sobre {topic} #shorts"

                # Fail-safe: Ensure description exists
                if "description" not in script_json:
                     script_json["description"] = f"Did you know this about {topic}? 😱 #shorts #nature #facts"

                # Fail-safe: Ensure scenes exist
                if "scenes" not in script_json or not script_json["scenes"]:
                    print(f"[LLM] WARNING: Generated script for {topic} has NO SCENES. Retrying...")
                    continue # Try again
                
                # CLEANING & PROCESSING (Power Words)
                POWER_WORDS = [
                    "deadly", "toxic", "poisonous", "dangerous", "killer", "weird", "strange", 
                    "creepy", "scary", "monster", "nightmare", "huge", "tiny", "fast", "slow",
                    "secret", "unknown", "fact", "crazy", "insane", "ugly", "beautiful", "rare",
                    "impossible", "death", "blood", "venom", "fangs", "teeth", "eyes"
                ]
                
                for scene in script_json.get("scenes", []):
                    if "narration" in scene:
                        text = scene["narration"].replace("...", "").replace("..", "").strip()
                        
                        words = text.split()
                        has_uppercase = any(w.isupper() and len(w) > 1 for w in words)
                        
                        if not has_uppercase:
                            new_words = []
                            highlighted = False
                            for w in words:
                                clean_w = w.strip(".,!?'\"").lower()
                                if clean_w in POWER_WORDS:
                                    new_words.append(w.upper())
                                    highlighted = True
                                else:
                                    new_words.append(w)
                            
                            if not highlighted and len(words) > 0:
                                longest_w = max(words, key=len)
                                if len(longest_w) > 4: 
                                    new_words = [w.upper() if w == longest_w else w for w in new_words]
                            
                            text = " ".join(new_words)
                        
                        scene["narration"] = text
                    else:
                        # Fallback for missing narration
                        print(f"[LLM] WARNING: Scene {i} missing 'narration'. Adding empty string.")
                        scene["narration"] = ""
                    
                    # Ensure other keys exist to prevent crashes elsewhere
                    if "duration" not in scene: scene["duration"] = 3
                    if "visual_description" not in scene: scene["visual_description"] = topic
                
                # If valid, return immediately
                return script_json

            except json.JSONDecodeError:
                print(f"[LLM] Error decoding JSON (Attempt {attempt+1}).")
                # print(cleaned_text[:200] + "...")
                continue
            except Exception as e:
                print(f"[LLM] Unexpected error (Attempt {attempt+1}): {e}")
                continue

        # If all retries failed
        print(f"[LLM] CRITICAL: Failed to generate valid script for {topic} after {MAX_RETRIES} attempts. Using Fallback.")
        return self._get_mock_fallback(topic)

    def _get_mock_fallback(self, topic):
        # Fallback to the previous mock implementation if Ollama fails
        return {
            "title": f"MOCK: Curiosidades sobre {topic}",
            "topic": topic,
            "description": f"Impossible facts about {topic}! 🤯 #shorts #nature #mock",
            "scenes": [
                 {
                        "start_time": 0,
                        "duration": 4,
                        "narration": f"This is the {topic}, one of the weirdest creatures on Earth.",
                        "visual_description": f"Cinematic shot of {topic} in its habitat.",
                        "stock_search_term": topic,
                    },
                    {
                        "start_time": 4,
                        "duration": 4,
                        "narration": "Scientists were baffled when they first discovered it.",
                        "visual_description": f"Close up of {topic} face.",
                        "stock_search_term": f"{topic} close up",
                    },
                    {
                        "start_time": 8,
                        "duration": 4,
                        "narration": "It has a superpower that no other animal has.",
                        "visual_description": f"{topic} moving or hunting.",
                        "stock_search_term": f"{topic} action",
                    },
                     {
                        "start_time": 12,
                        "duration": 4,
                        "narration": "It can survive in environments that would kill a human instantly.",
                        "visual_description": f"{topic} environment landscape.",
                        "stock_search_term": f"{topic} habitat",
                    },
                    {
                        "start_time": 16,
                        "duration": 4,
                        "narration": "Did you know this existed?",
                        "visual_description": f"Epic final shot of {topic}.",
                        "stock_search_term": topic,
                    },
                    {
                        "start_time": 20,
                        "duration": 4,
                        "narration": f"Subscribe for more facts about the {topic}.",
                        "visual_description": f"{topic} looking at camera.",
                        "stock_search_term": topic,
                    }
            ]
        }

    async def suggest_topic(self, history_topics):
        """
        Asks the LLM for new unique animal topics and picks one that hasn't been used.
        Uses JSON mode to strictly enforce output format and avoid conversational leakage.
        """
        # Ask for a batch of 10 to increase odds of finding a unique one
        system_prompt = """You are an assistant that suggests unique, interesting animals for YouTube Shorts. 
        Return a JSON object with a single key 'animals' containing a list of 10 unique animal names.
        Example: {"animals": ["Axolotl", "Pangolin", "Cassowary"]}
        NO numbering, NO explanations, NO conversational text."""
        
        user_prompt = f"Suggest 10 unique animals that are NOT in this list: {history_topics}. Return strictly JSON."
        
        # Shared Backup List for both Retries Exhausted and Critical Errors
        import random
        BACKUP_ANIMALS = [
             "Axolotl", "Narwhal", "Pangolin", "Quokka", "Cassowary", 
             "Blobfish", "Tardigrade", "Platypus", "Echidna", "Fossa",
             "Okapi", "Shoebill Stork", "Mantis Shrimp", "Aye-Aye", "Kakapo",
             "Vampire Squid", "Goblin Shark", "Pink Fairy Armadillo", "Saiga Antelope", "Star-Nosed Mole"
        ]

        MAX_RETRIES = 3
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"[LLM] Topic Suggestion Attempt {attempt+1}/{MAX_RETRIES} (JSON Mode)...")
                response_text = await asyncio.to_thread(self._call_ollama, user_prompt, system_prompt, json_mode=True)
                
                if not response_text:
                    continue

                try:
                    # Clean potential markdown
                    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(cleaned_text)
                    candidates = data.get("animals", [])
                except json.JSONDecodeError:
                     print(f"[LLM] JSON Decode Error in Topic Suggestion: {response_text[:50]}...")
                     # Fallback: try to split by comma if JSON fails (unlikely in JSON mode but possible)
                     candidates = response_text.replace('\n', ',').split(',')

                
                # Normalize history once for efficient checking
                clean_history_list = []
                for h in history_topics:
                    norm = "".join(c for c in h if c.isalnum()).lower()
                    if norm:
                        clean_history_list.append(norm)

                
                for cand in candidates:
                    # Robust cleaning: 
                    # 1. Remove leading numbering (e.g. "1. ", "2)") BEFORE removing punctuation
                    import re
                    cand_str = str(cand).strip()
                    cand_str = re.sub(r'^\d+[\.\)]\s*', '', cand_str)
                    
                    # 2. General cleanup (quotes)
                    cand_str = cand_str.replace('"', '').replace('.', '').replace('*', '').strip()
                    cand_str = cand_str.split('(')[0].strip() # Remove (Scientific Name) if present in list
                    
                    
                    # 3. FILTER OUT CHATTY LINES (STRICT)
                    words = cand_str.split()
                    # Animals are rarely > 4 words (e.g. "Eastern Lowland Gorilla")
                    if len(words) > 4: 
                        continue
                        
                    lower_cand = cand_str.lower()
                    
                    # Blacklist of conversational starters/fillers
                    BLACKLIST = [
                        "here", "sure", "i have", "below", "certainly", "list", "includes", 
                        "suggest", "recommend", "how about", "what about", "try", "check", 
                        "if you", "you can", "note", "please", "following", "example", "animal"
                    ]
                    
                    if any(lower_cand.startswith(b) for b in BLACKLIST):
                        continue
                        
                    # Filter out phrases that look like sentences (verbs/pronouns)
                    if " you " in lower_cand or " i " in lower_cand or " we " in lower_cand:
                        continue

                    if cand_str and len(cand_str) > 2:
                        norm_cand = "".join(c for c in cand_str if c.isalnum()).lower()
                        
                        is_duplicate = False
                        for h in clean_history_list:
                             # Exact match
                             if norm_cand == h:
                                 is_duplicate = True
                                 break
                             # Containment Check (matches HistoryManager logic)
                             # Handles dirty history like "animalnameaxolotl" vs "axolotl"
                             if len(norm_cand) > 3 and len(h) > 3:
                                 if norm_cand in h or h in norm_cand:
                                     print(f"[LLM] Detected duplicate (containment): {cand_str} matches {h}")
                                     is_duplicate = True
                                     break
                        
                        if not is_duplicate:
                            print(f"[LLM] Selected unique topic from batch: {cand_str}")
                            return cand_str
                
                # If we get here, all candidates were duplicates
                print(f"\n## WARNING: BATCH {attempt+1} ALL DUPLICATES. RETRYING SEARCH... ##\n")
            
            except Exception as e:
                print(f"[LLM] Error suggesting topic (Attempt {attempt+1}): {e}")
                if attempt == MAX_RETRIES - 1:
                    print("\n!!! CRITICAL ERROR: MAX RETRIES EXHAUSTED OR CRASH. SWITCHING TO RESERVE LIST !!!\n")
        
        # --- FALLBACK STRATEGY (Shared) ---
        print("\n#############################################################")
        print("## CRITICAL: SEARCH FAILED. USING EMERGENCY RESERVE LIST   ##")
        print("#############################################################\n")
        
        random.shuffle(BACKUP_ANIMALS)
        
        for backup in BACKUP_ANIMALS:
             norm_backup = "".join(c for c in backup if c.isalnum()).lower()
             
             clean_history_backup = set()
             for h in history_topics:
                 norm = "".join(c for c in h if c.isalnum()).lower()
                 if norm:
                    clean_history_backup.add(norm)

             if norm_backup not in clean_history_backup:
                 print(f"\n!!! FALLBACK SELECTED: {backup} !!!\n")
                 return backup

        # If even backups are exhausted...
        fallback_topic = f"Deep Sea Creature {random.randint(1, 100)}"
        return fallback_topic
