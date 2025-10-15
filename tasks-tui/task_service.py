# task_service.py - The Model/Service Layer
# Handles all communication with the Google Tasks API.
# By keeping this separate, you can swap out the Google API client
# for another backend (e.g., a local file, another service) without
# changing the curses UI code.

from googleapiclient.discovery import build
from .auth import get_credentials

class TaskService:
    """
    Manages connections and data flow for Google Tasks.
    """
    def __init__(self):
        creds = get_credentials()
        self.service = build('tasks', 'v1', credentials=creds)
        self.active_list_id = self._get_default_task_list_id()

    def _get_default_task_list_id(self):
        """Fetches the ID of the first task list."""
        task_lists = self.get_task_lists()
        return task_lists[0]['id'] if task_lists else None

    def get_task_lists(self):
        """Fetches all available task lists."""
        results = self.service.tasklists().list().execute()
        return results.get('items', [])

    def get_tasks_for_list(self, list_id=None):
        """Fetches all tasks for the currently active list."""
        list_id = list_id or self.active_list_id
        if not list_id:
            return []
        results = self.service.tasks().list(tasklist=list_id).execute()
        return results.get('items', [])

    def add_task(self, list_id, title):
        """Adds a new task to the specified list."""
        if not list_id:
            return None
        task = {'title': title}
        result = self.service.tasks().insert(tasklist=list_id, body=task).execute()
        return result

    def toggle_task_status(self, list_id, task_id):
        """Toggles a task's status."""
        if not list_id:
            return None
        task = self.service.tasks().get(tasklist=list_id, task=task_id).execute()
        task['status'] = 'completed' if task.get('status') == 'needsAction' else 'needsAction'
        result = self.service.tasks().update(tasklist=list_id, task=task_id, body=task).execute()
        return result

    def delete_task(self, list_id, task_id):
        if not list_id:
            return None
        result = self.service.tasks().delete(tasklist=list_id, task=task_id).execute()
        return result

    def rename_task(self, list_id, task_id, new_name):
        if not list_id:
            return None
        task = self.service.tasks().get(tasklist=list_id, task=task_id).execute()
        task['title'] = new_name
        result = self.service.tasks().patch(tasklist=list_id, task=task_id, body=task).execute()
        return result

    def set_active_list(self, list_id):
        """Changes the task list currently being viewed."""
        self.active_list_id = list_id
        return True

    def add_list(self, list_name):
        list_body = {'title': list_name}
        result = self.service.tasklists().insert(body=list_body).execute()
        return result

    def delete_list(self, list_id):
        result = self.service.tasklists().delete(tasklist=list_id).execute()
        return result
        
# You would handle the API credential flow here:
# if __name__ == '__main__':
#     # Example of fetching real data in production
#     service = TaskService(api_credentials=...)
#     print(service.get_task_lists())

