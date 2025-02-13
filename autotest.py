"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TestRunHandler(FileSystemEventHandler):
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def on_modified(self, event):
        print("Change detected, running tests...")
        try:
            result = subprocess.run(
                ["pytest", "--maxfail=1", "--disable-warnings", "-q"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            print(result.stdout)
            print(result.stderr)
        except Exception as e:
            print(f"Error running tests: {e}")

def watch_and_run_tests(repo_path):
    event_handler = TestRunHandler(repo_path)
    observer = Observer()
    observer.schedule(event_handler, path=repo_path, recursive=True)
    observer.start()
    print(f"Autonomous test runner started for {repo_path}. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
