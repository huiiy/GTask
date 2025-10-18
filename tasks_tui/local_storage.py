
import os
import json

STORAGE_FILE = 'local_tasks.json'

def load_data():
    """Loads task data from the local JSON storage file."""
    if not os.path.exists(STORAGE_FILE):
        return {'task_lists': [], 'tasks': {}}
    try:
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'task_lists': [], 'tasks': {}}

def save_data(data):
    """Saves task data to the local JSON storage file."""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        # Handle cases where the file cannot be written
        pass
