import unittest

from screentime.activity import normalize_app_name, sanitize_window_title


class FocusPrivacyTests(unittest.TestCase):
    def test_browser_titles_are_not_retained(self) -> None:
        self.assertEqual(sanitize_window_title("chrome.exe", "Private page title"), "")

    def test_non_browser_titles_are_trimmed(self) -> None:
        self.assertEqual(sanitize_window_title("notepad.exe", " Notes "), "Notes")

    def test_executable_names_are_normalized(self) -> None:
        self.assertEqual(normalize_app_name("chrome.exe"), "Google Chrome")
        self.assertEqual(normalize_app_name("ChatGPT.exe"), "ChatGPT")
        self.assertEqual(normalize_app_name("my_notes_app.exe"), "My Notes App")

    def test_versioned_python_names_share_one_label(self) -> None:
        self.assertEqual(normalize_app_name("pythonw3.13.exe"), "Python")
        self.assertEqual(normalize_app_name("Pythonw3.13"), "Python")

    def test_display_names_keep_meaningful_dots(self) -> None:
        self.assertEqual(normalize_app_name("Tetr.Io"), "Tetr.Io")


if __name__ == "__main__":
    unittest.main()
