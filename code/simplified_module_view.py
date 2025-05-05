
import os
import ast
import subprocess
from collections import defaultdict

TOP_N = 15


def compute_class_locs_and_files(folder_path):
    class_locs = {}
    class_files = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(
                    root, file), folder_path).replace("\\", "/")
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        loc = sum(1 for line in lines if line.strip()
                                  and not line.strip().startswith("#"))
                        tree = ast.parse("".join(lines))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                class_locs[node.name] = loc
                                class_files[node.name] = rel_path
                except:
                    continue
    return class_locs, class_files


def compute_churn(folder_path):
    churn = defaultdict(int)
    result = subprocess.run(
        ["git", "-C", folder_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    files = result.stdout.splitlines()
    for file in files:
        if file.endswith(".py"):
            churn[file.strip()] += 1
    return churn


def extract_import_dependencies(folder_path):
    imports = defaultdict(set)
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                src = os.path.relpath(os.path.join(
                    root, file), folder_path).replace("\\", "/")
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom) and node.module:
                                module_path = node.module.replace(
                                    ".", "/") + ".py"
                                imports[src].add(module_path)
                except:
                    continue
    return imports


def generate_module_dot(folder_path, output_file="simplified_architecture.dot"):
    locs, class_files = compute_class_locs_and_files(folder_path)
    churns = compute_churn(folder_path)

    scores = {}
    for cls, loc in locs.items():
        file = class_files[cls]
        churn = churns.get(file, 0)
        scores[cls] = loc + churn

    top_classes = sorted(scores, key=scores.get, reverse=True)[:TOP_N]
    top_modules = set(class_files[cls] for cls in top_classes)

    imports = extract_import_dependencies(folder_path)

    with open(output_file, "w") as f:
        f.write("digraph G {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box, style=filled, fillcolor=lightblue];\n")
        for mod in top_modules:
            label = f"{mod}\\n(contains top class)"
            f.write(f'  "{mod}" [label="{label}"]\n')
        for src in top_modules:
            for tgt in imports.get(src, []):
                if tgt in top_modules:
                    f.write(f'  "{src}" -> "{tgt}";\n')
        f.write("}\n")
    print(f"Simplified module architecture written to {output_file}")


if __name__ == "__main__":
    generate_module_dot("api", "simplified_architecture.dot")
