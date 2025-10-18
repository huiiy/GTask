from googleapiclient.discovery import build
from .auth import get_credentials
from dateutil.parser import isoparse
from . import local_storage

class TaskService:
    """
    Manages connections and data flow for Google Tasks, with a local cache.
    """
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('tasks', 'v1', credentials=self.creds)
        self.data = local_storage.load_data()
        self.dirty = False

        if not self.data or not self.data['task_lists']:
            self.sync_from_google()

        self.active_list_id = self._get_default_task_list_id()

    def _get_default_task_list_id(self):
        """Gets the ID of the first task list from local data."""
        return self.data['task_lists'][0]['id'] if self.data['task_lists'] else None

    def sync_from_google(self):
        """Fetches all data from Google Tasks and updates the local cache."""
        task_lists = self.service.tasklists().list().execute().get('items', [])
        self.data['task_lists'] = task_lists
        self.data['tasks'] = {}
        for task_list in task_lists:
            list_id = task_list['id']
            tasks = self.service.tasks().list(tasklist=list_id).execute().get('items', [])
            self.data['tasks'][list_id] = tasks
        self.save_local_data()

    def save_local_data(self):
        """Saves the current in-memory data to the local storage."""
        local_storage.save_data(self.data)
        self.dirty = False

    def get_task_lists(self):
        """Fetches all available task lists from the local cache."""
        return [lst for lst in self.data.get('task_lists', []) if not lst.get('deleted')]

    def get_tasks_for_list(self, list_id=None):
        """Fetches all tasks for the specified list from the local cache."""
        list_id = list_id or self.active_list_id
        if not list_id:
            return []
        return [task for task in self.data['tasks'].get(list_id, []) if not task.get('deleted')]

    def add_task(self, list_id, title):
        """Adds a new task to the specified list in the local cache."""
        if not list_id:
            return None
        # This is a temporary ID. Real ID will be assigned after sync.
        import time
        temp_id = f'temp_{int(time.time())}'
        task = {'title': title, 'id': temp_id, 'status': 'needsAction'}
        if list_id not in self.data['tasks']:
            self.data['tasks'][list_id] = []
        self.data['tasks'][list_id].append(task)
        self.dirty = True
        return task

    def toggle_task_status(self, list_id, task_id):
        """Toggles a task's status in the local cache."""
        if not list_id:
            return None
        for task in self.data['tasks'].get(list_id, []):
            if task['id'] == task_id:
                task['status'] = 'completed' if task.get('status') == 'needsAction' else 'needsAction'
                self.dirty = True
                return task
        return None

    def delete_task(self, list_id, task_id):
        """Deletes a task from the local cache."""
        if not list_id:
            return None
        tasks = self.data['tasks'].get(list_id, [])
        for i, task in enumerate(tasks):
            if task['id'] == task_id:
                # Mark as deleted for sync purposes
                tasks[i]['deleted'] = True 
                self.dirty = True
                return True
        return False

    def rename_task(self, list_id, task_id, new_name):
        """Renames a task in the local cache."""
        if not list_id:
            return None
        for task in self.data['tasks'].get(list_id, []):
            if task['id'] == task_id:
                task['title'] = new_name
                self.dirty = True
                return task
        return None

    def change_date_task(self, list_id, task_id, date_str):
        """Changes a task's due date in the local cache."""
        if not list_id:
            return None
        try:
            date_obj = isoparse(date_str)
            due_date_rfc3339 = date_obj.isoformat() + 'Z'
            for task in self.data['tasks'].get(list_id, []):
                if task['id'] == task_id:
                    task['due'] = due_date_rfc3339
                    self.dirty = True
                    return task
            return None
        except (isoparse.ParserError, ValueError):
            return None

    def change_detail_task(self, list_id, task_id, detail):
        """Changes a task's notes in the local cache."""
        if not list_id:
            return None
        for task in self.data['tasks'].get(list_id, []):
            if task['id'] == task_id:
                task['notes'] = detail
                self.dirty = True
                return task
        return None

    def get_task(self, list_id, task_id):
        """Gets a task from the local cache."""
        if not list_id:
            return None
        for task in self.data['tasks'].get(list_id, []):
            if task['id'] == task_id:
                return task
        return None

    def set_active_list(self, list_id):
        """Changes the task list currently being viewed."""
        self.active_list_id = list_id
        return True

    def add_list(self, list_name):
        """Adds a new list to the local cache."""
        import time
        temp_id = f'temp_list_{int(time.time())}'
        list_body = {'title': list_name, 'id': temp_id}
        self.data['task_lists'].append(list_body)
        self.data['tasks'][temp_id] = []
        self.dirty = True
        return list_body

    def delete_list(self, list_id):
        """Deletes a list from the local cache."""
        for i, task_list in enumerate(self.data['task_lists']):
            if task_list['id'] == list_id:
                # Mark as deleted for sync purposes
                self.data['task_lists'][i]['deleted'] = True
                self.dirty = True
                return True
        return False

    def rename_list(self, list_id, new_title):
        """Renames a list in the local cache."""
        if not list_id:
            return None

        # Find the index of the list to update
        list_index = -1
        for i, task_list in enumerate(self.data['task_lists']):
            if task_list['id'] == list_id:
                list_index = i
                break

        if list_index == -1:
            return None

        # Update title in local cache first
        self.data['task_lists'][list_index]['title'] = new_title
        self.dirty = True
        return True

    def sync_to_google(self):
        """Syncs local changes to Google Tasks."""
        if not self.dirty:
            return

        # Sync lists
        new_list_id_map = {}
        for i, task_list in enumerate(self.data['task_lists']):
            if task_list.get('deleted'):
                if not task_list['id'].startswith('temp_list_'):
                    try:
                        self.service.tasklists().delete(tasklist=task_list['id']).execute()
                    except Exception as e:
                        # Handle case where list is already deleted
                        pass
            elif task_list['id'].startswith('temp_list_'):
                old_id = task_list['id']
                new_list_body = {'title': task_list['title']}
                new_list = self.service.tasklists().insert(body=new_list_body).execute()
                self.data['task_lists'][i] = new_list
                new_list_id_map[old_id] = new_list['id']

        # Update task list IDs in tasks data
        for old_id, new_id in new_list_id_map.items():
            if old_id in self.data['tasks']:
                self.data['tasks'][new_id] = self.data['tasks'].pop(old_id)

        # Sync tasks
        for list_id, tasks in self.data['tasks'].items():
            if list_id.startswith('temp_list_'):
                continue # These tasks will be handled with the new list id

            for i, task in enumerate(tasks):
                if task.get('deleted'):
                    if not task['id'].startswith('temp_'):
                        try:
                            self.service.tasks().delete(tasklist=list_id, task=task['id']).execute()
                        except Exception as e:
                            # Handle case where task is already deleted
                            pass
                elif task['id'].startswith('temp_'):
                    new_task_body = {'title': task['title']}
                    if 'due' in task: new_task_body['due'] = task['due']
                    if 'notes' in task: new_task_body['notes'] = task['notes']
                    new_task = self.service.tasks().insert(tasklist=list_id, body=new_task_body).execute()
                    tasks[i] = new_task
                else:
                    # Update existing task
                    try:
                        google_task = self.service.tasks().get(tasklist=list_id, task=task['id']).execute()
                        if (google_task.get('title') != task.get('title') or
                            google_task.get('status') != task.get('status') or
                            google_task.get('due') != task.get('due') or
                            google_task.get('notes') != task.get('notes')):
                            updated_task = self.service.tasks().update(tasklist=list_id, task=task['id'], body=task).execute()
                            tasks[i] = updated_task
                    except Exception as e:
                        # Handle case where task no longer exists on google
                        pass

        self.save_local_data()