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


if __name__ == "__main__":
    unittest.main()
