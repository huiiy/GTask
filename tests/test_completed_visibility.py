import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tasks_tui.main import AppState, handle_input
from tasks_tui.task_service import TaskService


class CompletedVisibilityTests(unittest.TestCase):
    def setUp(self):
        # Exercise the real local service without authentication or network writes.
        self.service = TaskService.__new__(TaskService)
        self.service.active_list_id = 'list'
        self.service.dirty = False
        self.service.data = {
            'task_lists': [{'id': 'list'}, {'id': 'other'}],
            'tasks': {
                'list': [
                    {'id': 'done', 'status': 'completed'},
                    {'id': 'open', 'status': 'needsAction'},
                    {'id': 'parent', 'status': 'needsAction'},
                    {'id': 'child-done', 'parent': 'parent', 'status': 'completed'},
                    {'id': 'child-open', 'parent': 'parent', 'status': 'needsAction'},
                ],
                'other': [{'id': 'other-done', 'status': 'completed'}],
            },
        }
        self.state = AppState(self.service)
        self.ui = SimpleNamespace(active_panel='tasks', selected_task_idx=0)

    def press(self, key):
        with patch('tasks_tui.main.getch', return_value=ord(key)):
            self.assertTrue(handle_input(None, self.state, self.ui))

    def ids(self):
        return [task['id'] for task in self.state.tasks]

    def test_default_filter_counts_and_toggle_preserve_selection_and_data(self):
        self.assertEqual(self.ids(), ['open', 'parent'])
        self.assertEqual(self.state.task_counts, {'list': 2, 'other': 0})
        self.press('v')
        self.assertEqual(self.ids(), ['done', 'open', 'parent'])
        self.assertEqual(self.ui.selected_task_idx, 1)
        self.assertEqual(self.state.task_counts['list'], 3)
        self.press('v')
        self.assertEqual(self.ids(), ['open', 'parent'])
        self.assertEqual(self.ui.selected_task_idx, 0)
        self.assertFalse(self.service.dirty)
        self.assertEqual(len(self.service.data['tasks']['list']), 5)

    def test_subtasks_and_return_after_filter_changes(self):
        self.press('v')
        self.ui.selected_task_idx = 2
        self.press('l')
        self.assertEqual(self.ids(), ['child-done', 'child-open'])
        self.press('v')
        self.assertEqual(self.ids(), ['child-open'])
        self.press('h')
        self.assertEqual(self.ids()[self.ui.selected_task_idx], 'parent')

    def test_completing_last_visible_task_clamps_selection_and_handles_empty(self):
        self.ui.selected_task_idx = 1
        self.press('c')
        self.assertEqual(self.ids(), ['open'])
        self.assertEqual(self.ui.selected_task_idx, 0)
        self.press('c')
        self.assertEqual(self.ids(), [])
        self.press('c')
        self.press('v')
        self.assertEqual(len(self.state.tasks), 3)
        self.press('c')
        self.assertEqual(self.state.tasks[0]['status'], 'needsAction')

    def test_preference_survives_list_switch_and_refresh(self):
        self.state.change_active_list('other')
        self.assertEqual(self.ids(), [])
        self.press('v')
        self.assertEqual(self.ids(), ['other-done'])
        self.state.change_active_list('list')
        self.state.refresh_data()
        self.assertEqual(self.ids(), ['done', 'open', 'parent'])

    def test_completion_in_lists_panel_does_not_modify_tasks(self):
        self.ui.active_panel = 'lists'
        self.press('c')
        self.assertFalse(self.service.dirty)


if __name__ == '__main__':
    unittest.main()
