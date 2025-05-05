
import os
import ast
import subprocess

TOP_N = 15


def extract_class_relations(folder_path):
    usage_edges = []
    inheritance_edges = []
    class_files = {}

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                class_files[node.name] = rel_path
                                for base in node.bases:
                                    if isinstance(base, ast.Name):
                                        inheritance_edges.append(
                                            (node.name, base.id))
                            elif isinstance(node, ast.Assign):
                                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                                    if hasattr(node.targets[0], 'id'):
                                        usage_edges.append(
                                            (rel_path, node.value.func.id))
                except:
                    continue
    return class_files, inheritance_edges, usage_edges


def compute_class_locs(folder_path):
    locs = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        loc = sum(1 for line in lines if line.strip()
                                  and not line.strip().startswith("#"))
                        tree = ast.parse("".join(lines))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                locs[node.name] = loc
                except:
                    continue
    return locs


def compute_churn(folder_path):
    churn = {}
    result = subprocess.run(
        ["git", "-C", folder_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    files = result.stdout.splitlines()
    for file in files:
        if file.endswith(".py"):
            file = os.path.basename(file.strip())
            churn[file] = churn.get(file, 0) + 1
    return churn


def generate_graphviz_diagram(folder_path, output_file="architecture.dot"):
    class_files, inheritance, usage = extract_class_relations(folder_path)
    locs = compute_class_locs(folder_path)
    churns = compute_churn(folder_path)

    scores = {}
    for cls in class_files:
        loc = locs.get(cls, 0)
        churn = churns.get(os.path.basename(class_files[cls]), 0)
        scores[cls] = loc + churn

    top_classes = set(sorted(scores, key=scores.get, reverse=True)[:TOP_N])
    edges = []
    for a, b in inheritance + usage:
        if a in top_classes and b in top_classes:
            edges.append((a, b))

    with open(output_file, "w") as f:
        f.write("digraph G {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box, style=filled, fillcolor=lightblue];\n")
        for cls in top_classes:
            label = f"{cls}\\nLOC: {locs.get(cls, 0)}\\nChurn: {churns.get(
                os.path.basename(class_files.get(cls, '')), 0)}"
            f.write(f'  "{cls}" [label="{label}"];\n')
        for a, b in edges:
            f.write(f'  "{a}" -> "{b}";\n')
        f.write("}\n")
    print(f"Wrote architecture diagram to {output_file}")


if __name__ == "__main__":
    generate_graphviz_diagram("api", "architecture.dot")
