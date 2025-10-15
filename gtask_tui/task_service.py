# task_service.py - The Model/Service Layer
# Handles all communication with the Google Tasks API.
# By keeping this separate, you can swap out the Google API client
# for another backend (e.g., a local file, another service) without
# changing the curses UI code.

import uuid

# --- MOCK DATA STRUCTURE ---
# In a real app, this data would be fetched from the Google Tasks API.
MOCK_TASK_LISTS = [
    {"id": "list1", "title": "My Tasks", "default": True},
    {"id": "list2", "title": "Work Project"},
]

MOCK_TASKS = {
    "list1": [
        {"id": str(uuid.uuid4()), "title": "Buy groceries", "status": "needsAction"},
        {"id": str(uuid.uuid4()), "title": "Pay bills (Completed)", "status": "completed"},
    ],
    "list2": [
        {"id": str(uuid.uuid4()), "title": "Review Q3 report", "status": "needsAction"},
        {"id": str(uuid.uuid4()), "title": "Schedule team meeting", "status": "needsAction"},
    ],
}

class TaskService:
    """
    Manages connections and data flow for Google Tasks.
    In a real implementation, this is where you would handle OAuth2,
    API client initialization, and network calls.
    """
    def __init__(self, api_credentials=None):
        # NOTE: In a real app, this is where you would initialize
        # the Google Tasks API client, handle authentication, etc.
        # For this example, we use mock data.
        self.active_list_id = "list1"
        self.api_client = None  # Placeholder for the actual Google API client

    def get_task_lists(self):
        """Fetches all available task lists."""
        # Replace this with a call to service.tasklists().list().execute()
        return MOCK_TASK_LISTS

    def get_tasks_for_list(self, list_id=None):
        """Fetches all tasks for the currently active list."""
        list_id = list_id or self.active_list_id
        # Replace this with a call to service.tasks().list(tasklist=list_id).execute()
        return MOCK_TASKS.get(list_id, [])

    def add_task(self, list_id, title):
        """Adds a new task to the specified list."""
        # Replace this with service.tasks().insert(tasklist=list_id, body={'title': title}).execute()
        new_task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "status": "needsAction"
        }
        MOCK_TASKS[list_id].append(new_task)
        return new_task

    def toggle_task_status(self, list_id, task_id):
        """Toggles a task between needsAction and completed."""
        # Replace with service.tasks().update(...) call
        for task in MOCK_TASKS[list_id]:
            if task["id"] == task_id:
                if task["status"] == "needsAction":
                    task["status"] = "completed"
                    task["title"] = task["title"] + " (Completed)"
                else:
                    task["status"] = "needsAction"
                    task["title"] = task["title"].replace(" (Completed)", "")
                return task
        return None

    def set_active_list(self, list_id):
        """Changes the task list currently being viewed."""
        if list_id in MOCK_TASKS:
            self.active_list_id = list_id
            return True
        return False

# You would handle the API credential flow here:
# if __name__ == '__main__':
#     # Example of fetching real data in production
#     service = TaskService(api_credentials=...)
#     print(service.get_task_lists())

