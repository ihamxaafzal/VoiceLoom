import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import launcher


class StartupTests(unittest.TestCase):
    def test_missing_project_files_are_identified(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            with patch.object(launcher, 'BASE', Path(folder)):
                with self.assertRaisesRegex(RuntimeError, 'app.py'):
                    launcher.preflight()

    def test_missing_dependencies_identify_setup_action(self):
        with patch.object(launcher, 'REQUIRED', ()), patch.object(launcher.importlib.util, 'find_spec', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'Run setup.bat'):
                launcher.preflight()

    def test_native_import_crash_is_in_diagnostic_report(self):
        failed = SimpleNamespace(returncode=-1073741819, stdout='', stderr='Native library failed')
        report = io.StringIO()
        with patch.object(launcher, 'REQUIRED', ()), patch.object(launcher, 'MODULES', ('torch',)), \
             patch.object(launcher.subprocess, 'run', return_value=failed), contextlib.redirect_stdout(report):
            self.assertEqual(launcher.diagnose(), 1)
        self.assertIn('torch: FAILED', report.getvalue())
        self.assertIn('Native library failed', report.getvalue())


if __name__ == '__main__':
    unittest.main()
