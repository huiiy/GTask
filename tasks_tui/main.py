# main.py - The Controller Layer / Entry Point
# Initializes the application, connects the TaskService (Model) and
# the UIManager (View), and runs the main event loop.

from unicurses import *
from .task_service import TaskService
from .ui_manager import UIManager
import sys
from dateutil.parser import ParserError, isoparse
import os
import subprocess
import tempfile
from unicurses import wrapper

def open_editor_for_task_notes(stdscr, app_state, ui_manager):
    """Opens an editor for the task notes."""
    selected_task = app_state.tasks[ui_manager.selected_task_idx]
    initial_content = selected_task.get('notes', '')

    editor = os.environ.get('EDITOR', 'vim')  # Default to vim

    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode='w+', encoding='utf-8') as tf:
        tf.write(initial_content)
        temp_path = tf.name

    # Suspend curses and open the editor
    def_prog_mode()
    endwin()
    subprocess.call([editor, temp_path])
    # Resume curses
    reset_prog_mode()
    doupdate()

    with open(temp_path, 'r', encoding='utf-8') as tf:
        new_note = tf.read()

    os.remove(temp_path)

    if new_note != initial_content:
        app_state.service.change_detail_task(app_state.active_list_id, selected_task['id'], new_note)
        app_state.refresh_data()

def is_valid_date(date_str):
    try:
        isoparse(date_str)
        return True
    except (ParserError, ValueError):
        return False

# Global State Management (simplified for TUI)
class AppState:
    """Holds the application's current state and data."""
    def __init__(self, task_service):
        self.service = task_service
        self.task_lists = self.service.get_task_lists()
        self.active_list_id = self.service.active_list_id
        self.current_parent_task_id = None
        self.filtered_tasks_cache = {}  # Cache for filtered tasks
        self.task_counts = {}
        self.tasks = self.get_tasks_for_active_list()
        self.list_buffer = ""
        self.task_buffer = ""
        self.parent_task_id_stack = []
        self.parent_task_idx_stack = []
        self.calculate_task_counts()
        self.show_help = False

    def calculate_task_counts(self):
        """Calculates the number of tasks in each list."""
        for task_list in self.task_lists:
            list_id = task_list['id']
            self.task_counts[list_id] = len(self.service.get_tasks_for_list(list_id))

    def get_tasks_for_active_list(self):
        """Retrieves tasks for the active list, using cache if possible."""
        if self.current_parent_task_id:
            return self.service.get_subtasks(self.active_list_id, self.current_parent_task_id)
        else:
            if self.active_list_id not in self.filtered_tasks_cache or self.service.dirty:
                # If not in cache or data is dirty, fetch and cache it
                tasks = self.service.get_tasks_for_list(self.active_list_id)
                self.filtered_tasks_cache[self.active_list_id] = tasks
            return self.filtered_tasks_cache[self.active_list_id]

    def refresh_data(self):
        """Refreshes all data from the service layer and clears the cache."""
        self.task_lists = self.service.get_task_lists()
        self.filtered_tasks_cache.clear()  # Invalidate the cache
        self.tasks = self.get_tasks_for_active_list()
        self.calculate_task_counts()

    def change_active_list(self, list_id):
        """Updates the active list and fetches new tasks, using the cache."""
        if self.service.set_active_list(list_id):
            self.active_list_id = list_id
            self.current_parent_task_id = None
            self.tasks = self.get_tasks_for_active_list()
            return True
        return False

def handle_input(stdscr, app_state, ui_manager):
    """
    Main input handler. Maps key presses to application actions.
    """
    try:
        key = getch()
    except curses.error:
        return True # Ignore curses errors on getch()

    # Quitting
    if key in [ord('q'), ord('Q')]:
        if app_state.service.dirty:
            ui_manager.start_sync_animation()
            app_state.service.sync_to_google()
            ui_manager.stop_sync_animation()
        return False

    if key == KEY_RESIZE:
        return True # Triggers a redraw

    # Movement
    elif key == KEY_UP or key == ord('k'):
        if ui_manager.active_panel == 'tasks':
            ui_manager.update_task_selection(app_state.tasks, -1)
        elif ui_manager.active_panel == 'lists':
            ui_manager.update_list_selection(app_state.task_lists, -1)
    elif key == KEY_DOWN or key == ord('j'):
        if ui_manager.active_panel == 'tasks':
            ui_manager.update_task_selection(app_state.tasks, 1)
        elif ui_manager.active_panel == 'lists':
            ui_manager.update_list_selection(app_state.task_lists, 1)
    elif key == KEY_LEFT or key == ord('h'):
        if app_state.current_parent_task_id:
            app_state.current_parent_task_id = app_state.parent_task_id_stack.pop()
            app_state.refresh_data()
            if app_state.parent_task_idx_stack:
                ui_manager.selected_task_idx = app_state.parent_task_idx_stack.pop()
        elif ui_manager.active_panel == 'tasks':
            ui_manager.toggle_panel()
    elif key == KEY_RIGHT or key == ord('l'):
        if ui_manager.active_panel == 'lists':
            selected_list = app_state.task_lists[ui_manager.selected_list_idx]
            if app_state.active_list_id != selected_list['id']:
                app_state.change_active_list(selected_list["id"])
                ui_manager.selected_task_idx = 0 # Reset task selection
            ui_manager.toggle_panel()
        elif ui_manager.active_panel == 'tasks' and app_state.tasks:
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.parent_task_id_stack.append(app_state.current_parent_task_id)
            app_state.parent_task_idx_stack.append(ui_manager.selected_task_idx)
            app_state.current_parent_task_id = selected_task['id']
            app_state.refresh_data()
            ui_manager.selected_task_idx = 0
            
    # Action Keys

    elif key == ord('c'):
            # Toggle task status
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.toggle_task_status(app_state.active_list_id, selected_task["id"])
            app_state.refresh_data() # Refresh display after change

    elif key == ord('w'):
        ui_manager.start_sync_animation()
        app_state.service.sync_to_google()
        ui_manager.stop_sync_animation()
        app_state.refresh_data()

    elif key == ord('r'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            new_title = ui_manager.get_user_input("New Task Title: ")
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.rename_task(app_state.active_list_id, selected_task["id"], new_title)
            app_state.refresh_data() # Refresh display after change
        elif ui_manager.active_panel == 'lists' and app_state.task_lists:
            new_title = ui_manager.get_user_input("New List Title: ")
            if new_title:
                selected_list = app_state.task_lists[ui_manager.selected_list_idx]
                app_state.service.rename_list(selected_list['id'], new_title)
                app_state.refresh_data()

    elif key == ord('a'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            new_date = ui_manager.get_user_input("Due Date: ")
            if is_valid_date(new_date):
                selected_task = app_state.tasks[ui_manager.selected_task_idx]
                app_state.service.change_date_task(app_state.active_list_id, selected_task['id'], new_date)
                app_state.refresh_data()
            else:
                ui_manager.show_temporary_message(f"Invalid date format: '{new_date}'")


    elif key == ord('i'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            open_editor_for_task_notes(stdscr, app_state, ui_manager)



    elif key == ord('d'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.task_buffer = app_state.service.get_task(app_state.active_list_id, selected_task['id'])
            app_state.service.delete_task(app_state.active_list_id, selected_task["id"])
            app_state.refresh_data() # Refresh display after change
            # Adjust selection after deletion
            if ui_manager.selected_task_idx >= len(app_state.tasks) and len(app_state.tasks) > 0:
                ui_manager.selected_task_idx = len(app_state.tasks) - 1
        elif ui_manager.active_panel == 'lists' and app_state.task_.lists:
            selected_list = app_state.task_lists[ui_manager.selected_list_idx]
            confirm = ui_manager.get_user_input(f"Delete list '{selected_list['title']}'? (y/n): ")
            if confirm.lower() == 'y':
                app_state.list_buffer = selected_list['title']
                app_state.service.delete_list(selected_list["id"])
                app_state.task_lists = app_state.service.get_task_lists()
                if app_state.task_lists:
                    app_state.change_active_list(app_state.task_lists[0]['id'])
                else:
                    app_state.active_list_id = None
                app_state.refresh_data()

    elif key == ord('p'):
        if ui_manager.active_panel == 'tasks':
            if app_state.tasks:
                current_task = app_state.tasks[ui_manager.selected_task_idx]
                unfiltered_tasks = app_state.service.data['tasks'][app_state.active_list_id]
                unfiltered_index = -1
                for i, task in enumerate(unfiltered_tasks):
                    if task['id'] == current_task['id']:
                        unfiltered_index = i
                        break
                
                if unfiltered_index != -1:
                    app_state.service.add_task_body(app_state.active_list_id, app_state.task_buffer, unfiltered_index)
                else:
                    # Should not happen, but as a fallback, append to the end
                    app_state.service.add_task_body(app_state.active_list_id, app_state.task_buffer)
            else:
                # Pasting into an empty list
                app_state.service.add_task_body(app_state.active_list_id, app_state.task_buffer)
            app_state.refresh_data()
        else:
            app_state.service.add_list(app_state.list_buffer)
            app_state.refresh_data()

    # Add New Task
    elif key == ord('o'):
        if ui_manager.active_panel == 'tasks':
            new_title = ui_manager.get_user_input("New Task Title: ")
            if new_title:
                if app_state.current_parent_task_id:
                    app_state.service.add_task(app_state.active_list_id, new_title, parent=app_state.current_parent_task_id)
                else:
                    app_state.service.add_task(app_state.active_list_id, new_title)
                app_state.refresh_data() # Fetch and display the new task
        else:
            new_title = ui_manager.get_user_input("New List Title: ")
            if new_title:
                app_state.service.add_list(new_title)
                app_state.refresh_data()

    elif key == ord('?'):
        ui_manager.toggle_help()



    return True # Keep the loop running

def main_loop(stdscr):
    """The main application loop function required by curses.wrapper."""
    # 1. Initialization
    task_service = TaskService()
    ui_manager = UIManager(stdscr)
    app_state = AppState(task_service)

    # Disable cursor visibility for a cleaner TUI
    curs_set(0)
    noecho()
    cbreak()
    keypad(stdscr, True)

    ui_manager.start_sync_animation()
    app_state.service.sync_from_google()
    ui_manager.stop_sync_animation()
    app_state.refresh_data()

    running = True
    while running:
        # 2. Draw the UI based on current state
        try:
            parent_task = None
            if app_state.current_parent_task_id:
                parent_task = app_state.service.get_task(app_state.active_list_id, app_state.current_parent_task_id)

            parent_ids = app_state.service.get_parent_task_ids(app_state.active_list_id)

            ui_manager.draw_layout(
                app_state.task_lists,
                app_state.tasks,
                app_state.active_list_id,
                app_state.task_counts,
                parent_task=parent_task,
                parent_ids=parent_ids
            )
            doupdate()
        except Exception as e:
            # Handles window resize errors gracefully
            ui_manager.show_temporary_message(f"Error: {e}")

        # 3. Handle User Input
        running = handle_input(stdscr, app_state, ui_manager)

def cli():
    try:
        wrapper(main_loop)
    except Exception as e:
        # Print the error before exiting the terminal session
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    cli()