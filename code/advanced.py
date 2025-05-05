import ast
import os
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import subprocess


class ClassUsageExtractor(ast.NodeVisitor):
    def __init__(self):
        self.current_class = None
        self.class_defs = set()
        self.inheritance = []  # (child, parent)
        # {user_class: {used_class1, used_class2, ...}}
        self.usage = defaultdict(set)
        self.assignments = {}  # Tracks variable names → class names (simple)

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.class_defs.add(node.name)

        # Inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.inheritance.append((node.name, base.id))
            elif isinstance(base, ast.Attribute):
                self.inheritance.append((node.name, base.attr))

        self.generic_visit(node)
        self.current_class = None  # Reset when leaving class scope

    def visit_Assign(self, node):
        # Track simple instantiations: x = ClassName()
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            class_name = node.value.func.id
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.assignments[target.id] = class_name
                    if self.current_class:
                        self.usage[self.current_class].add(class_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        # Detect calls like: x.method() → try to see if x is an instance of a known class
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            class_name = self.assignments.get(var_name)
            if class_name and self.current_class:
                self.usage[self.current_class].add(class_name)
        self.generic_visit(node)


def extract_relations_from_folder(folder):
    extractor = ClassUsageExtractor()
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=path)
                        extractor.visit(tree)
                except Exception as e:
                    print(f"[!] Skipped {path}: {e}")
    return extractor.inheritance, extractor.usage


def get_class_locs(folder_path):
    class_locs = {}

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                module_path = os.path.relpath(full_path, folder_path).replace(
                    "/", ".").replace("\\", ".").replace(".py", "")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source = f.read()
                        tree = ast.parse(source)
                        lines = source.splitlines()

                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                class_name = f"{module_path}.{node.name}"
                                start_line = node.lineno - 1
                                end_line = max([child.lineno for child in ast.walk(
                                    node) if hasattr(child, 'lineno')], default=start_line)

                                loc = 0
                                for i in range(start_line, end_line):
                                    line = lines[i].strip()
                                    if line and not line.startswith("#"):
                                        loc += 1
                                class_locs[class_name] = loc

                except Exception as e:
                    print(f"Error parsing {full_path}: {e}")

    return class_locs


def get_churn_by_file(repo_path):
    churn = {}
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    file_changes = result.stdout.splitlines()

    for file in file_changes:
        if file.strip().endswith(".py"):
            churn[file] = churn.get(file, 0) + 1

    return churn


def map_churn_to_classes(folder_path, churn_by_file):
    class_churn = {}

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                churn_value = churn_by_file.get(rel_path, 0)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                class_name = node.name
                                class_churn[class_name] = churn_value
                except Exception as e:
                    print(f"Error processing churn for {rel_path}: {e}")

    return class_churn


def save_plotly_graph(inheritance, usage, output_file="zeeguu_class_relations.html", class_locs=None, class_churns=None):
    G = nx.DiGraph()

    # Add edges and build full node list
    nodes = set()
    for child, parent in inheritance:
        G.add_edge(child, parent, relation="inherits")
        nodes.update([child, parent])
    for user_class, used_classes in usage.items():
        for used_class in used_classes:
            G.add_edge(user_class, used_class, relation="uses")
            nodes.update([user_class, used_class])

    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='gray'),
                            hoverinfo='none', mode='lines')

    node_x = []
    node_y = []
    node_size = []
    node_text = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        loc = class_locs.get(node, 10) if class_locs else 10
        churn = class_churns.get(node, 0) if class_churns else 0
        size = max(10, min(loc, 100))  # scale size reasonably
        node_x.append(x)
        node_y.append(y)
        node_size.append(size)
        node_color.append(churn)  # use churn as color scale
        node_text.append(f"{node}<br>LOC: {loc}<br>Churn: {churn}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[n for n in G.nodes()],
        textposition="bottom center",
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale="Bluered",
            showscale=True,
            colorbar=dict(title="Churn"),
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=dict(text="Class Relationships with LOC",
                                   font=dict(size=20)),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False))
                    )
    fig.write_html(output_file)
    print(f"Saved interactive graph to {output_file}")


inheritance, usage = extract_relations_from_folder("api")
locs = get_class_locs("api")

# Step 2: Refine mapping using short names (only if unique)
short_name_index = defaultdict(list)
for full_name, loc in locs.items():
    short_name = full_name.split(".")[-1]
    short_name_index[short_name].append(loc)

# Only keep names that map unambiguously to one class
short_class_locs = {
    name: locs[0]
    for name, locs in short_name_index.items()
    if len(locs) == 1
}

churn_by_file = get_churn_by_file("api")
class_churn = map_churn_to_classes("api", churn_by_file)

save_plotly_graph(inheritance, usage,
                  "zeeguu_class_relations.html", class_locs=short_class_locs, class_churns=class_churn)

G = nx.DiGraph()

# Add inheritance edges
for child, parent in inheritance:
    G.add_edge(child, parent, label="inherits")

# Add usage edges
for user_class, used_classes in usage.items():
    for used_class in used_classes:
        G.add_edge(user_class, used_class, label="uses")

# Draw the graph
pos = nx.spring_layout(G, seed=42)
edge_labels = nx.get_edge_attributes(G, "label")

plt.figure(figsize=(14, 10))
nx.draw(G, pos, with_labels=True, node_size=2000,
        node_color="lightyellow", font_size=10, arrows=True)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")
plt.title("Class Relationships in Zeeguu API (Inheritance + Usage)")
plt.tight_layout()
plt.savefig("class_relations.png", dpi=300)  # Save the figure
