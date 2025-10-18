# ui_manager.py - The View Layer
# Handles all screen drawing, window splitting, and curses-specific logic.
# It receives data from the main application logic and draws it.
# It should not contain any Google Tasks API interaction logic.

import curses
from dateutil.parser import isoparse
import time
import threading

class UIManager:
    """
    Manages the curses screen layout and drawing.
    """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()
        self.active_panel = "lists" # 'lists' or 'tasks'
        self.selected_list_idx = 0
        self.selected_task_idx = 0
        self.syncing = False
        self.animation_thread = None
        self.show_help = False

    def setup_colors(self):
        """Initializes color pairs for the TUI."""
        # Use simple color pairs suitable for a terminal
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Completed
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Header
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Active List
        curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Selected

    def _draw_border(self, win, title):
        """Draws a simple box border and title."""
        h, w = win.getmaxyx()
        win.box()
        title_str = f" {title} "
        win.addstr(0, 2, title_str, curses.color_pair(3) | curses.A_BOLD)

    def draw_layout(self, lists, tasks, active_list_id, task_counts, parent_task=None, parent_ids=None):
        """Draws the main two-panel layout."""
        h, w = self.stdscr.getmaxyx()

        # 1. Calculate window sizes
        list_width = max(25, w // 4) # Lists take up at least 25 chars or 1/4th of the screen
        task_width = w - list_width

        # 2. Create window objects
        # Lists Window (Left Panel)
        list_win = self.stdscr.subwin(h, list_width, 0, 0)
        # Tasks Window (Right Panel)
        task_win = self.stdscr.subwin(h, task_width, 0, list_width)

        # 3. Draw content inside the windows
        self._draw_list_panel(list_win, lists, active_list_id, task_counts)
        self._draw_task_panel(task_win, tasks, parent_task, parent_ids)

        # 4. Refresh all windows
        list_win.noutrefresh()
        task_win.noutrefresh()

        if self.show_help:
            self._draw_help_panel()

    def _draw_help_panel(self):
        """Draws a help panel with controls."""
        h, w = self.stdscr.getmaxyx()
        help_h = 15
        help_w = 60
        help_y = (h - help_h) // 2
        help_x = (w - help_w) // 2

        help_win = self.stdscr.subwin(help_h, help_w, help_y, help_x)
        help_win.erase()
        self._draw_border(help_win, "Help (?)")

        controls = [
            ("q", "Quit and Sync"),
            ("w", "Write and Sync"),
            ("h/j/k/l", "Select List/Task/Subtask"),
            ("c", "Complete Toggle"),
            ("r", "Rename Task/List"),
            ("a", "Add Due Date"),
            ("i", "Insert Note"),
            ("d", "Delete Task/List"),
            ("p", "Paste Task/List"),
            ("o", "Open Task"),
            ("?", "Help Toggle"),
        ]

        for i, (key, desc) in enumerate(controls):
            help_win.addstr(i + 1, 2, f"{key:<20} {desc}")

        help_win.noutrefresh()

    def _draw_list_panel(self, win, lists, active_list_id, task_counts):
        """Draws the Task List titles."""
        win.erase()
        self._draw_border(win, "Task Lists (L)")
        max_y, max_x = win.getmaxyx()

        for idx, list_item in enumerate(lists):
            list_title = list_item.get("title", "Untitled List")
            list_id = list_item.get("id")
            task_count = task_counts.get(list_id, 0)
            display_title = f"{list_title} ({task_count})"

            is_active = list_item["id"] == active_list_id
            is_selected = self.active_panel == 'lists' and idx == self.selected_list_idx
            y_pos = idx + 1 # Start drawing content on line 1

            if y_pos >= max_y - 1:
                break # Avoid drawing off the screen

            attr = curses.A_NORMAL
            if is_active:
                attr |= curses.color_pair(4) # Yellow for the currently loaded list
            if is_selected:
                attr |= curses.color_pair(5)

            win.addstr(y_pos, 1, f"{display_title:<{max_x-2}}", attr)
            win.addstr(max_y - 1, max_x - 10, "(?) Help", curses.A_DIM)


    def _draw_task_panel(self, win, tasks, parent_task=None, parent_ids=None):
        """Draws the individual Tasks."""
        win.erase()
        title = f"Tasks in {parent_task['title']}" if parent_task else "Tasks (T)"
        self._draw_border(win, title)
        max_y, max_x = win.getmaxyx()

        if parent_ids is None:
            parent_ids = set()

        if not tasks:
            attr = curses.color_pair(5) if self.active_panel == 'tasks' else curses.A_DIM
            win.addstr(1, 2, "No tasks in this list.", attr)
            return

        for idx, task in enumerate(tasks):
            task_title = task.get("title", "Untitled Task")
            status = task.get("status", "needsAction")
            is_selected = self.active_panel == 'tasks' and idx == self.selected_task_idx
            y_pos = idx + 1 # Start drawing content on line 1

            if y_pos >= max_y - 2:
                break # Avoid drawing off the screen

            attr = curses.A_NORMAL
            symbol = "[ ]"

            if status == "completed":
                attr = curses.color_pair(2)
                symbol = "[X]"

            if is_selected:
                attr = curses.color_pair(5)

            # Pad the title to ensure highlight fills the line
            due_date_str = ""
            if "due" in task:
                try:
                    # Google Tasks API returns 'due' in RFC 3339 format
                    due_date = isoparse(task["due"])
                    due_date_str = f" (Due: {due_date.strftime("%Y-%m-%d")})"
                except ValueError:
                    due_date_str = " (Invalid Date)"

            note_indicator = "*" if "notes" in task and task["notes"] else " "
            has_children_indicator = " >" if task['id'] in parent_ids else ""

            display_line = f"{symbol} {task_title}{note_indicator}{has_children_indicator}{due_date_str}"
            # Truncate if too long, ensuring space for selection highlight
            win.addstr(y_pos, 1, display_line[:max_x - 2], attr)

    def update_task_selection(self, tasks, direction):
        """Moves the task selection cursor (up/down)."""
        if self.active_panel != 'tasks' or not tasks:
            return

        max_idx = len(tasks) - 1
        new_idx = self.selected_task_idx + direction

        if new_idx < 0:
            self.selected_task_idx = 0
        elif new_idx > max_idx:
            self.selected_task_idx = max_idx
        else:
            self.selected_task_idx = new_idx

    def update_list_selection(self, lists, direction):
        """Moves the list selection cursor (up/down)."""
        if self.active_panel != 'lists' or not lists:
            return

        max_idx = len(lists) - 1
        new_idx = self.selected_list_idx + direction

        if new_idx < 0:
            self.selected_list_idx = 0
        elif new_idx > max_idx:
            self.selected_list_idx = max_idx
        else:
            self.selected_list_idx = new_idx

    def toggle_panel(self):
        """Switches between the list panel and the task panel."""
        self.active_panel = 'tasks' if self.active_panel == 'lists' else 'lists'

    def toggle_help(self):
        """Toggles the help display."""
        self.show_help = not self.show_help

    def get_user_input(self, prompt="Input: "):
        """
        Gets a text string from the user at the bottom of the screen.
        This is a common helper function needed in curses applications.
        """
        h, w = self.stdscr.getmaxyx()
        input_win = self.stdscr.subwin(1, w, h - 1, 0)
        input_win.erase()
        input_win.addstr(0, 0, prompt, curses.color_pair(0))
        input_win.refresh()

        input_string = ""
        try:
            input_win.keypad(True)
            while True:
                char = input_win.getch()
                if char == 27: # Escape key
                    input_string = ""
                    break
                elif char == curses.KEY_ENTER or char == 10 or char == 13:
                    break
                elif char == curses.KEY_BACKSPACE or char == 127 or char == 8:
                    if len(input_string) > 0:
                        input_string = input_string[:-1]
                        input_win.addstr(0, len(prompt) + len(input_string), " ")
                        input_win.move(0, len(prompt) + len(input_string))
                else:
                    input_string += chr(char)
                    input_win.addstr(0, len(prompt) + len(input_string) - 1, chr(char))
                input_win.refresh()
        finally:
            input_win.erase()
            input_win.refresh()

        return input_string

    def show_temporary_message(self, message):
        """Displays a message on the bottom line for a short duration."""
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 2, 1, message, curses.A_REVERSE)
        self.stdscr.refresh()
        time.sleep(1)
        # Clear the line
        self.stdscr.addstr(h - 2, 1, " " * (w - 2))
        self.stdscr.refresh()

    def _sync_animation(self):
        """The actual animation loop to be run in a thread."""
        braille_patterns = ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"]
        i = 0
        while self.syncing:
            h, w = self.stdscr.getmaxyx()
            message = f" {braille_patterns[i % len(braille_patterns)]} Syncing"
            self.stdscr.addstr(h - 2, 1, message, curses.A_NORMAL)
            self.stdscr.refresh()
            time.sleep(0.1)
            i += 1
        # Clear the animation message
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 2, 1, " " * (w - 2)) # Clear the line
        self.stdscr.refresh()

    def start_sync_animation(self):
        """Starts the sync animation in a separate thread."""
        if not self.syncing:
            self.syncing = True
            self.animation_thread = threading.Thread(target=self._sync_animation)
            self.animation_thread.start()

    def stop_sync_animation(self):
        """Stops the sync animation."""
        if self.syncing:
            self.syncing = False
            self.animation_thread.join()

