"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import time
import difflib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DiffHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file_path = file_path
        self.last_content = self._read_file()

    def _read_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

    def on_modified(self, event):
        if event.src_path == self.file_path:
            new_content = self._read_file()
            diff = difflib.unified_diff(self.last_content, new_content, fromfile="Before", tofile="After")
            print("\n".join(diff))
            self.last_content = new_content

def live_diff_view(file_path):
    event_handler = DiffHandler(file_path)
    observer = Observer()
    observer.schedule(event_handler, path=file_path, recursive=False)
    observer.start()
    print(f"Live diff view started for {file_path}. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
