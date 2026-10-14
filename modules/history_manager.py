import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, history_file="history.json"):
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4)

    @staticmethod
    def _normalize_topic(topic):
        """Normalize topic string for comparison (alphanumeric only, lowercase)."""
        return "".join(c for c in topic if c.isalnum()).lower()

    def is_unique(self, topic):
        """Checks if a topic is similar to previously generated ones."""
        norm_topic = self._normalize_topic(topic)

        for item in self.history:
            norm_history = self._normalize_topic(item.get("topic", ""))

            # Check for exact match
            if norm_topic == norm_history:
                return False

            # Check if one is fully contained in the other (e.g. "The Axolotl" vs "Axolotl")
            if len(norm_topic) > 3 and len(norm_history) > 3:
                if norm_topic in norm_history or norm_history in norm_topic:
                    return False

        return True

    def add_entry(self, topic, video_id=None):
        entry = {
            "topic": topic,
            "date": datetime.now().isoformat(),
            "video_id": video_id
        }
        self.history.append(entry)
        self.save_history()
