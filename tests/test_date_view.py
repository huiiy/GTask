import unittest
from datetime import date
from unittest.mock import patch

from tasks_tui.task_dates import date_section, due_date, sort_tasks
from tasks_tui.main import AppState, handle_input
from tasks_tui.task_service import TaskService
from tasks_tui.ui_manager import UIManager


def task(name, due=None, **extra):
    return dict(id=name, title=name, due=due, **extra)


class DateViewTests(unittest.TestCase):
    def test_chronological_stable_order_and_bad_dates(self):
        tasks = [task('none'), task('later', '2026-09-17T00:00:00Z'),
                 task('old', '2026-09-01'), task('same', '2026-09-17'),
                 task('bad', 'invalid'), task('empty', '')]
        self.assertEqual([t['id'] for t in sort_tasks(tasks)],
                         ['old', 'later', 'same', 'none', 'bad', 'empty'])
        self.assertEqual(tasks[0]['id'], 'none')
        self.assertEqual(due_date(task('offset', '2026-09-17T00:00:00+12:00')), date(2026, 9, 17))

    def test_sections(self):
        today = date(2026, 9, 14)
        for due, label in [('2026-09-13', 'Overdue'), ('2026-09-14', 'Today'),
                           ('2026-09-15', 'Tomorrow'), ('2026-09-17', 'Thu, Sep 17'),
                           ('2027-01-01', 'Fri, Jan 1, 2027'), (None, 'No date')]:
            self.assertEqual(date_section(task('t', due), today), label)

    def make_state(self):
        service = TaskService.__new__(TaskService)
        service.active_list_id = 'list'
        service.dirty = False
        service.data = {'task_lists': [{'id': 'list', 'title': 'List'}], 'tasks': {
            'list': [task('undated'), task('dated', '2026-09-15'),
                     task('child', '2026-09-10', parent='dated'),
                     task('deleted', '2026-09-01', deleted=True)]}}
        return AppState(service)

    def test_controller_order_and_selection_after_date_edit(self):
        state = self.make_state()
        ui = UIManager.__new__(UIManager)
        ui.active_panel = 'tasks'
        ui.selected_task_idx = 1
        self.assertEqual([t['id'] for t in state.tasks], ['dated', 'undated'])
        with patch('tasks_tui.main.getch', return_value=ord('a')), patch.object(
                ui, 'get_user_input', return_value='2026-09-01'):
            handle_input(None, state, ui)
        self.assertEqual(state.tasks[ui.selected_task_idx]['id'], 'undated')
        self.assertEqual(ui.selected_task_idx, 0)
        state.current_parent_task_id = 'dated'
        state.refresh_data()
        self.assertEqual([t['id'] for t in state.tasks], ['child'])

    def test_headers_navigation_and_scroll(self):
        ui = UIManager.__new__(UIManager)
        ui.active_panel = 'tasks'
        ui.selected_task_idx = 0
        ui.task_scroll_offset = 0
        tasks = [task(str(i), f'2026-09-{i + 1:02d}') for i in range(20)] + [task('last')]
        with patch('tasks_tui.ui_manager.getmaxyx', return_value=(8, 60)), \
             patch('tasks_tui.ui_manager.date_section', side_effect=lambda t: date_section(t, date(2026, 9, 14))), \
             patch('tasks_tui.ui_manager.werase'), \
             patch.object(ui, '_draw_border'), \
             patch('tasks_tui.ui_manager.color_pair', return_value=0), \
             patch('tasks_tui.ui_manager.mvwaddstr') as draw:
            ui._draw_task_panel(None, tasks)
            self.assertEqual(draw.call_args_list[0].args[3], 'Overdue')
            for _ in tasks:
                ui.update_task_selection(tasks, 1)
                ui._draw_task_panel(None, tasks)
            self.assertEqual(ui.selected_task_idx, len(tasks) - 1)
            self.assertGreater(ui.task_scroll_offset, 0)
            visible = [call.args[3] for call in draw.call_args_list[-5:]]
            self.assertIn('No date', visible)
            self.assertTrue(any('last' in line for line in visible))
            ui.update_task_selection(tasks, -100)
            ui._draw_task_panel(None, tasks)
            self.assertEqual(ui.task_scroll_offset, 0)


if __name__ == '__main__':
    unittest.main()
