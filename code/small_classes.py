import os
import ast
import subprocess
from collections import defaultdict


def count_small_and_stable_classes(folder_path, loc_threshold=60, churn_threshold=10):

    class_locs = {}
    class_files = {}
    churn_counts = defaultdict(int)

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        tree = ast.parse("".join(lines))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                start = node.lineno - 1
                                end = max((child.lineno for child in ast.walk(
                                    node) if hasattr(child, 'lineno')), default=start)
                                loc = sum(1 for line in lines[start:end] if line.strip(
                                ) and not line.strip().startswith("#"))
                                class_locs[node.name] = loc
                                class_files[node.name] = rel_path
                except:
                    continue

    result = subprocess.run(
        ["git", "-C", folder_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    for line in result.stdout.splitlines():
        line = line.strip().replace("\\", "/")
        if line.endswith(".py"):
            churn_counts[line] += 1

    count = 0
    for cls, loc in class_locs.items():
        file_path = class_files.get(cls, "")
        churn = churn_counts.get(file_path, 0)
        if loc < loc_threshold and churn < churn_threshold:
            count += 1

    print(f"Number of classes with < {loc_threshold} LOC and < {
          churn_threshold} commits: {count}")


def count_large_and_active_classes(folder_path, loc_threshold=100, churn_threshold=15):

    class_locs = {}
    class_files = {}
    churn_counts = defaultdict(int)

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        tree = ast.parse("".join(lines))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                start = node.lineno - 1
                                end = max((child.lineno for child in ast.walk(
                                    node) if hasattr(child, 'lineno')), default=start)
                                loc = sum(1 for line in lines[start:end] if line.strip(
                                ) and not line.strip().startswith("#"))
                                class_locs[node.name] = loc
                                class_files[node.name] = rel_path
                except:
                    continue

    result = subprocess.run(
        ["git", "-C", folder_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    for line in result.stdout.splitlines():
        line = line.strip().replace("\\", "/")
        if line.endswith(".py"):
            churn_counts[line] += 1

    count = 0
    for cls, loc in class_locs.items():
        file_path = class_files.get(cls, "")
        churn = churn_counts.get(file_path, 0)
        if loc >= loc_threshold and churn >= churn_threshold:
            count += 1

    print(f"Number of classes with >= {loc_threshold} LOC and >= {
          churn_threshold} commits: {count}")


# Example usage
count_small_and_stable_classes("api")

count_large_and_active_classes("api")
