
import os
import ast
import subprocess
import networkx as nx
import plotly.graph_objects as go
from collections import defaultdict

EXCLUDED_FILES = {"__init__.py"}
EXCLUDED_PREFIXES = {"test_", "scripts/", "tools/"}


def should_exclude(file_path):
    base = os.path.basename(file_path)
    if base in EXCLUDED_FILES:
        return True
    if any(base.startswith(prefix) or file_path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return True
    return False


def get_package_name(file_path):
    parts = file_path.split("/")
    if len(parts) > 1:
        return ".".join(parts[:-1])
    return parts[0].replace(".py", "")


def get_aggregated_locs(folder_path):
    locs = defaultdict(int)
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                if should_exclude(rel_path):
                    continue
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        loc = sum(1 for line in lines if line.strip()
                                  and not line.strip().startswith("#"))
                        pkg = get_package_name(rel_path)
                        locs[pkg] += loc
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
    return dict(locs)


def get_aggregated_churn(folder_path):
    churn = defaultdict(int)
    result = subprocess.run(
        ["git", "-C", folder_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    file_changes = result.stdout.splitlines()
    for file in file_changes:
        file = file.strip().replace("\\", "/")
        if file.endswith(".py") and not should_exclude(file):
            pkg = get_package_name(file)
            churn[pkg] += 1
    return dict(churn)


def get_package_dependencies(folder_path):
    deps = set()
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                if should_exclude(rel_path):
                    continue
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=rel_path)
                        src_pkg = get_package_name(rel_path)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                                tgt_path = node.module.replace(
                                    ".", "/") + ".py"
                                tgt_pkg = get_package_name(tgt_path)
                                if src_pkg != tgt_pkg:
                                    deps.add((src_pkg, tgt_pkg))
                except Exception as e:
                    print(f"Failed to parse {rel_path}: {e}")
    return list(deps)


def visualize_aggregated_module_graph(folder_path, output_file="aggregated_module_view.html"):
    locs = get_aggregated_locs(folder_path)
    churn = get_aggregated_churn(folder_path)
    edges = get_package_dependencies(folder_path)

    G = nx.DiGraph()
    for module in set(locs) | set(churn):
        G.add_node(module)

    for src, tgt in edges:
        G.add_edge(src, tgt)

    pos = nx.spring_layout(G, seed=42)

    node_x, node_y, node_size, node_color, node_text = [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        loc = locs.get(node, 10)
        ch = churn.get(node, 0)
        node_size.append(max(10, min(loc, 100)))
        node_color.append(ch)
        node_text.append(f"{node}<br>LOC: {loc}<br>Churn: {ch}")

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    fig = go.Figure(
        data=[
            go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(
                width=1, color='gray'), hoverinfo='none'),
            go.Scatter(
                x=node_x, y=node_y, mode='markers+text',
                marker=dict(size=node_size, color=node_color, colorscale="Bluered",
                            showscale=True, colorbar=dict(title="Churn")),
                text=[n for n in G.nodes()],
                hovertext=node_text,
                hoverinfo='text',
                textposition='bottom center'
            )
        ],
        layout=go.Layout(
            title=dict(
                text="Aggregated Package Dependency View (LOC + Churn)", font=dict(size=20)),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)
        )
    )
    fig.write_html(output_file)
    print(f"Saved interactive aggregated view to: {output_file}")


# Example usage:
visualize_aggregated_module_graph("api", "aggregated_module_view.html")
