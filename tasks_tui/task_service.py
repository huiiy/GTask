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
        self.initial_sync_completed = False

        if not self.data or not self.data['task_lists']:
            self.sync_from_google()
            self.initial_sync_completed = True

        self.active_list_id = self._get_default_task_list_id()

    def _get_default_task_list_id(self):
        """Gets the ID of the first task list from local data."""
        return self.data['task_lists'][0]['id'] if self.data['task_lists'] else None

    def sync_from_google(self):
        """Fetches all data from Google Tasks and updates the local cache."""
        if self.initial_sync_completed:
            return
        task_lists = self.service.tasklists().list().execute().get('items', [])
        self.data['task_lists'] = task_lists
        self.data['tasks'] = {}
        for task_list in task_lists:
            list_id = task_list['id']
            tasks = self.service.tasks().list(tasklist=list_id, showHidden=True).execute().get('items', [])
            if tasks:
                tasks.sort(key=lambda t: t.get('position', ''))
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
        return [task for task in self.data['tasks'].get(list_id, []) if not task.get('deleted') and not task.get('parent')]

    def get_subtasks(self, list_id, parent_task_id):
        """Fetches all subtasks for the specified parent task from the local cache."""
        if not list_id or not parent_task_id:
            return []
        
        subtasks = []
        for task in self.data['tasks'].get(list_id, []):
            if not task.get('deleted') and task.get('parent') == parent_task_id:
                subtasks.append(task)
        return subtasks

    def add_task(self, list_id, title, parent=None):
        """Adds a new task to the specified list in the local cache."""
        if not list_id:
            return None
        # This is a temporary ID. Real ID will be assigned after sync.
        import time
        temp_id = f'temp_{int(time.time())}'
        task = {'title': title, 'id': temp_id, 'status': 'needsAction'}
        if parent:
            task['parent'] = parent
        if list_id not in self.data['tasks']:
            self.data['tasks'][list_id] = []
        self.data['tasks'][list_id].append(task)
        self.dirty = True
        return task

    def add_task_body(self, list_id, task_body, index=None):
        """Adds a task from a task object to the specified list in the local cache."""
        if not list_id or not task_body:
            return None
        
        new_task = task_body.copy()
        new_task.pop('id', None)
        new_task.pop('deleted', None)

        # This is a temporary ID. Real ID will be assigned after sync.
        import time
        temp_id = f'temp_{int(time.time())}'
        new_task['id'] = temp_id

        if list_id not in self.data['tasks']:
            self.data['tasks'][list_id] = []
        
        if index is not None:
            self.data['tasks'][list_id].insert(index, new_task)
        else:
            self.data['tasks'][list_id].append(new_task)
        self.dirty = True
        return new_task

    def toggle_task_status(self, list_id, task_id):
        """Toggles a task's status in the local cache, and cascades to subtasks if completing."""
        if not list_id:
            return None

        tasks = self.data['tasks'].get(list_id, [])
        
        # Find the task and toggle its status
        toggled_task = None
        for task in tasks:
            if task['id'] == task_id:
                new_status = 'completed' if task.get('status') == 'needsAction' else 'needsAction'
                task['status'] = new_status
                self.dirty = True
                toggled_task = task
                break
                
        if not toggled_task:
            return None

        # If the task was completed, complete all its subtasks
        if toggled_task.get('status') == 'completed':
            self._cascade_complete(list_id, task_id)
                
        return toggled_task

    def _cascade_complete(self, list_id, parent_id):
        """Recursively completes all subtasks of a given parent."""
        tasks = self.data['tasks'].get(list_id, [])
        
        child_tasks_ids = [task['id'] for task in tasks if task.get('parent') == parent_id]
        
        for child_id in child_tasks_ids:
            for task in tasks:
                if task['id'] == child_id:
                    task['status'] = 'completed'
                    self.dirty = True
                    self._cascade_complete(list_id, child_id)
                    break

    def delete_task(self, list_id, task_id):
        """Deletes a task and all its subtasks from the local cache."""
        if not list_id:
            return None

        # Find the task and mark it as deleted
        tasks = self.data['tasks'].get(list_id, [])
        task_found = False
        for i, task in enumerate(tasks):
            if task['id'] == task_id:
                tasks[i]['deleted'] = True
                self.dirty = True
                task_found = True
                break
        
        if not task_found:
            return False

        # Find and delete child tasks
        child_tasks = []
        for task in tasks:
            if task.get('parent') == task_id:
                child_tasks.append(task['id'])
                
        for child_id in child_tasks:
            self.delete_task(list_id, child_id)
            
        return True

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

    def get_parent_task_ids(self, list_id):
        """Returns a set of task IDs that are parents."""
        if not list_id:
            return set()
        
        parent_ids = set()
        for task in self.data['tasks'].get(list_id, []):
            if task.get('parent'):
                parent_ids.add(task['parent'])
        return parent_ids

    def get_children_count(self, list_id, task_id):
        """Returns the number of children for a given task."""
        if not list_id:
            return 0
        count = 0
        for task in self.data['tasks'].get(list_id, []):
            if task.get('parent') == task_id:
                count += 1
        return count

    def get_children_counts(self, list_id):
        """Returns a dictionary mapping task IDs to their children count."""
        if not list_id:
            return {}
        counts = {}
        for task in self.data['tasks'].get(list_id, []):
            if task.get('parent'):
                parent_id = task.get('parent')
                if parent_id not in counts:
                    counts[parent_id] = 0
                counts[parent_id] += 1
        return counts

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
        if not self.dirty:
            return

        # Fetch all google lists for comparison
        google_lists_map = {lst['id']: lst for lst in self.service.tasklists().list().execute().get('items', [])}

        # Sync lists
        for i, task_list in enumerate(self.data['task_lists']):
            if task_list.get('deleted'):
                if not task_list['id'].startswith('temp_'):
                    try:
                        self.service.tasklists().delete(tasklist=task_list['id']).execute()
                    except Exception as e:
                        pass  # Already deleted
            elif task_list['id'].startswith('temp_list_'):
                # This is a new list, create it
                new_list_body = {'title': task_list['title']}
                new_list = self.service.tasklists().insert(body=new_list_body).execute()
                
                # Update the local list with the new ID
                old_id = task_list['id']
                self.data['task_lists'][i] = new_list

                # Update the tasks with the new list ID
                if old_id in self.data['tasks']:
                    self.data['tasks'][new_list['id']] = self.data['tasks'].pop(old_id)

            else:
                # Check for renames
                google_list = google_lists_map.get(task_list['id'])
                if google_list and task_list.get('title') != google_list.get('title'):
                    self.service.tasklists().patch(tasklist=task_list['id'], body={'title': task_list.get('title')}).execute()

        # Remove deleted lists from local cache
        self.data['task_lists'] = [lst for lst in self.data['task_lists'] if not lst.get('deleted')]
        for list_id in list(self.data['tasks'].keys()):
            if list_id not in [lst['id'] for lst in self.data['task_lists']]:
                del self.data['tasks'][list_id]

        for list_id, local_tasks_list in self.data['tasks'].items():
            if list_id.startswith('temp_list_'):
                continue

            google_tasks_list = self.service.tasks().list(tasklist=list_id, showHidden=True).execute().get('items', [])
            google_tasks_map = {t['id']: t for t in google_tasks_list}

            # Handle new tasks (with temporary IDs)
            new_tasks = [t for t in local_tasks_list if t['id'].startswith('temp_')]
            id_map = {} # For mapping temp IDs to new Google IDs

            unprocessed_new_tasks = list(new_tasks)
            while unprocessed_new_tasks:
                processed_in_this_pass = 0
                remaining_tasks = []
                
                for task in unprocessed_new_tasks:
                    old_id = task['id']
                    parent_id = task.get('parent')
                    
                    new_parent_id = None
                    if parent_id:
                        if parent_id.startswith('temp_'):
                            new_parent_id = id_map.get(parent_id)
                        else:
                            new_parent_id = parent_id # It's a real ID
                    
                    if not parent_id or new_parent_id:
                        # Process this task
                        new_task_body = {'title': task['title']}
                        if 'due' in task: new_task_body['due'] = task['due']
                        if 'notes' in task: new_task_body['notes'] = task['notes']
                        if 'status' in task: new_task_body['status'] = task['status']
                        
                        new_task = self.service.tasks().insert(tasklist=list_id, body=new_task_body, parent=new_parent_id).execute()
                        id_map[old_id] = new_task['id']
                        task['id'] = new_task['id'] # Update the local task with the new ID
                        
                        processed_in_this_pass += 1
                    else:
                        remaining_tasks.append(task)
                        
                if processed_in_this_pass == 0 and remaining_tasks:
                    # Circular dependency or bug, add remaining as top-level
                    for task in remaining_tasks:
                        new_task_body = {'title': task['title']}
                        if 'due' in task: new_task_body['due'] = task['due']
                        if 'notes' in task: new_task_body['notes'] = task['notes']
                        if 'status' in task: new_task_body['status'] = task['status']
                        
                        new_task = self.service.tasks().insert(tasklist=list_id, body=new_task_body).execute()
                        task['id'] = new_task['id']
                    break
                    
                unprocessed_new_tasks = remaining_tasks

            # Handle updated tasks
            for task in local_tasks_list:
                if not task['id'].startswith('temp_') and task['id'] in google_tasks_map:
                    google_task = google_tasks_map[task['id']]
                    
                    update_body = {}
                    if task.get('title') != google_task.get('title'): update_body['title'] = task.get('title')
                    if task.get('notes') != google_task.get('notes'): update_body['notes'] = task.get('notes')
                    if task.get('due') != google_task.get('due'): update_body['due'] = task.get('due')
                    if task.get('status') != google_task.get('status'): update_body['status'] = task.get('status')
                    
                    if update_body:
                        self.service.tasks().patch(tasklist=list_id, task=task['id'], body=update_body).execute()

            # Handle deleted tasks
            deleted_tasks = [t for t in local_tasks_list if t.get('deleted')]
            for task in deleted_tasks:
                if not task['id'].startswith('temp_'):
                    try:
                        self.service.tasks().delete(tasklist=list_id, task=task['id']).execute()
                    except Exception as e:
                        pass # Already deleted

            # Remove deleted tasks from local cache
            self.data['tasks'][list_id] = [t for t in local_tasks_list if not t.get('deleted')]

        self.save_local_data()