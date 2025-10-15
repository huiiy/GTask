# main.py - The Controller Layer / Entry Point
# Initializes the application, connects the TaskService (Model) and
# the UIManager (View), and runs the main event loop.

import curses
from curses import wrapper
from .task_service import TaskService
from .ui_manager import UIManager
import sys

# Global State Management (simplified for TUI)
class AppState:
    """Holds the application's current state and data."""
    def __init__(self, task_service):
        self.service = task_service
        self.task_lists = self.service.get_task_lists()
        self.active_list_id = self.service.active_list_id
        self.tasks = self.service.get_tasks_for_list(self.active_list_id)

    def refresh_data(self):
        """Refreshes all data from the service layer."""
        self.task_lists = self.service.get_task_lists()
        self.tasks = self.service.get_tasks_for_list(self.active_list_id)

    def change_active_list(self, list_id):
        """Updates the active list and fetches new tasks."""
        if self.service.set_active_list(list_id):
            self.active_list_id = list_id
            self.tasks = self.service.get_tasks_for_list(self.active_list_id)
            return True
        return False

def handle_input(stdscr, app_state, ui_manager):
    """
    Main input handler. Maps key presses to application actions.
    """
    key = stdscr.getch()

    # Quitting
    if key in [ord('q'), ord('Q')]:
        return False

    # Movement
    elif key == curses.KEY_UP or key == ord('k'):
        if ui_manager.active_panel == 'tasks':
            ui_manager.update_task_selection(app_state.tasks, -1)
        elif ui_manager.active_panel == 'lists':
            ui_manager.update_list_selection(app_state.task_lists, -1)
    elif key == curses.KEY_DOWN or key == ord('j'):
        if ui_manager.active_panel == 'tasks':
            ui_manager.update_task_selection(app_state.tasks, 1)
        elif ui_manager.active_panel == 'lists':
            ui_manager.update_list_selection(app_state.task_lists, 1)
    elif key == curses.KEY_LEFT or key == ord('h'):
        if ui_manager.active_panel == 'tasks':
            ui_manager.toggle_panel()
    elif key == curses.KEY_RIGHT or key == ord('l'):
        if ui_manager.active_panel == 'lists':
            # TODO check if selected list is not current active list, reduce fetch time
            selected_list = app_state.task_lists[ui_manager.selected_list_idx]
            if app_state.active_list_id != selected_list['id']:
                app_state.change_active_list(selected_list["id"])
                ui_manager.selected_task_idx = 0 # Reset task selection
            ui_manager.toggle_panel()
            

    # Panel Switching
    elif key == ord('\t'): # TAB key
        ui_manager.toggle_panel()

    # Action Keys
    elif key == ord('\n'): # ENTER key
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            # Toggle task status
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.toggle_task_status(app_state.active_list_id, selected_task["id"])
            app_state.refresh_data() # Refresh display after change
        elif ui_manager.active_panel == 'lists' and app_state.task_lists:
            # Load selected list
            selected_list = app_state.task_lists[ui_manager.selected_list_idx]
            app_state.change_active_list(selected_list["id"])
            ui_manager.selected_task_idx = 0 # Reset task selection

    elif key == ord('c'):
            # Toggle task status
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.toggle_task_status(app_state.active_list_id, selected_task["id"])
            app_state.refresh_data() # Refresh display after change

    elif key == ord('w'):
        app_state.refresh_data()

    elif key == ord('r'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            new_title = ui_manager.get_user_input("New Task Title: ")
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.rename_task(app_state.active_list_id, selected_task["id"], new_title)
            app_state.refresh_data() # Refresh display after change
        elif ui_manager.active_panel == 'lists' and app_state.task_lists:
            new_title = ui_manager.get_user_input("New List Title: ")
            return

    elif key == ord('a'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            new_date = ui_manager.get_user_input("Due Date: ")
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.change_date_task(app_state.active_list_id, selected_task['id'], new_date)
            app_state.refresh_data()

    elif key == ord('i'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            new_note = ui_manager.get_user_input("Notes: ")
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.change_detail_task(app_state.active_list_id, selected_task['id'], new_note)
            app_state.refresh_data()



    elif key == ord('d'):
        if ui_manager.active_panel == 'tasks' and app_state.tasks:
            selected_task = app_state.tasks[ui_manager.selected_task_idx]
            app_state.service.delete_task(app_state.active_list_id, selected_task["id"])
            app_state.refresh_data() # Refresh display after change
        elif ui_manager.active_panel == 'lists' and app_state.task_lists:
            selected_list = app_state.task_lists[ui_manager.selected_list_idx]
            confirm = ui_manager.get_user_input(f"Delete list '{selected_list['title']}'? (y/n): ")
            if confirm.lower() == 'y':
                app_state.service.delete_list(selected_list["id"])
                app_state.task_lists = app_state.service.get_task_lists()
                if app_state.task_lists:
                    app_state.change_active_list(app_state.task_lists[0]['id'])
                else:
                    app_state.active_list_id = None
                app_state.refresh_data()

    # Add New Task
    elif key == ord('o'):
        if ui_manager.active_panel == 'tasks':
            new_title = ui_manager.get_user_input("New Task Title: ")
            if new_title:
                app_state.service.add_task(app_state.active_list_id, new_title)
                app_state.refresh_data() # Fetch and display the new task
        else:
            new_title = ui_manager.get_user_input("New List Title: ")
            if new_title:
                app_state.service.add_list(new_title)
                app_state.refresh_data()



    return True # Keep the loop running

def main_loop(stdscr):
    """The main application loop function required by curses.wrapper."""
    # 1. Initialization
    task_service = TaskService()
    ui_manager = UIManager(stdscr)
    app_state = AppState(task_service)

    # Disable cursor visibility for a cleaner TUI
    curses.curs_set(0)

    running = True
    while running:
        # 2. Draw the UI based on current state
        try:
            ui_manager.draw_layout(
                app_state.task_lists,
                app_state.tasks,
                app_state.active_list_id
            )
            curses.doupdate()
        except curses.error as e:
            # Handles window resize errors gracefully
            pass

        # 3. Handle User Input
        running = handle_input(stdscr, app_state, ui_manager)

def cli():
    try:
        # The wrapper handles initialization and safe cleanup of the curses environment
        wrapper(main_loop)
    except Exception as e:
        # Print the error before exiting the terminal session
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    cli()
