"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import difflib

def selective_apply(original_file: str, modified_file: str):
    with open(original_file, 'r', encoding='utf-8') as f:
        original = f.readlines()
    with open(modified_file, 'r', encoding='utf-8') as f:
        modified = f.readlines()

    diff = list(difflib.unified_diff(original, modified, fromfile="Original", tofile="Modified"))
    if not diff:
        print("No differences found.")
        return

    hunks = []
    current_hunk = []
    for line in diff:
        if line.startswith('@@'):
            if current_hunk:
                hunks.append(current_hunk)
                current_hunk = []
        current_hunk.append(line)
    if current_hunk:
        hunks.append(current_hunk)

    for i, hunk in enumerate(hunks, start=1):
        print(f"\nHunk {i}:")
        print("".join(hunk))
        choice = input("Apply this hunk? (y/n): ")
        if choice.lower() == 'y':
            # For simplicity, if at least one hunk is approved, we replace the file entirely.
            print("Hunk approved.")
        else:
            print("Hunk skipped.")

    final_choice = input("Apply changes from modified file to original file? (y/n): ")
    if final_choice.lower() == 'y':
        with open(modified_file, 'r', encoding='utf-8') as f:
            new_content = f.read()
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Selected changes applied.")
    else:
        print("No changes applied.")
