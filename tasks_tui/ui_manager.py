# ui_manager.py - The View Layer
# Handles all screen drawing, window splitting, and curses-specific logic.
# It receives data from the main application logic and draws it.
# It should not contain any Google Tasks API interaction logic.

import curses
from dateutil.parser import isoparse
import time

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

    def draw_layout(self, lists, tasks, active_list_id):
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
        self._draw_list_panel(list_win, lists, active_list_id)
        self._draw_task_panel(task_win, tasks)

        # 4. Refresh all windows
        list_win.noutrefresh()
        task_win.noutrefresh()

    def _draw_list_panel(self, win, lists, active_list_id):
        """Draws the Task List titles."""
        win.erase()
        self._draw_border(win, "Task Lists (L)")
        max_y, max_x = win.getmaxyx()

        for idx, list_item in enumerate(lists):
            list_title = list_item.get("title", "Untitled List")
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

            win.addstr(y_pos, 1, f"{list_title:<{max_x-2}}", attr)

        win.addstr(max_y - 1, 1, "Use A to Add List", curses.A_DIM)

    def _draw_task_panel(self, win, tasks):
        """Draws the individual Tasks."""
        win.erase()
        self._draw_border(win, "Tasks (T)")
        max_y, max_x = win.getmaxyx()

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

            display_line = f"{symbol} {task_title}{due_date_str}"
            # Truncate if too long, ensuring space for selection highlight
            win.addstr(y_pos, 1, display_line[:max_x - 2], attr)

        # Draw a help footer
        win.addstr(max_y - 1, 1, "ENTER: Toggle | "
                   "TAB: Switch Panel | "
                   "Q: Quit | "
                   "o: New Task |"
                   "w: Write and Sync", curses.A_DIM)

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

        # Set up for user input
        curses.echo()
        input_string = ""
        try:
            # max width is w - len(prompt) - 2 for borders/safety
            input_string = input_win.getstr(0, len(prompt), w - len(prompt) - 2).decode('utf-8')
        except:
            # Handle potential resize/error during input
            pass
        finally:
            curses.noecho()
            input_win.erase()
            input_win.refresh()

        return input_string

    def show_temporary_message(self, message):
        """Displays a message on the bottom line for a short duration."""
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 1, 0, message, curses.A_REVERSE)
        self.stdscr.refresh()
        time.sleep(1)
        # Clear the line
        self.stdscr.addstr(h - 1, 0, " " * (w - 1))
        self.stdscr.refresh()

