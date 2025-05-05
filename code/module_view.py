
import os
import ast
import subprocess
import networkx as nx
import plotly.graph_objects as go


def get_module_locs(folder_path):
    locs = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        loc = sum(1 for line in lines if line.strip()
                                  and not line.strip().startswith("#"))
                        locs[rel_path] = loc
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
    return locs


def get_module_churn(folder_path):
    churn = {}
    result = subprocess.run(
        ["git", "-C", folder_path, "log", "--pretty=format:", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    file_changes = result.stdout.splitlines()
    for file in file_changes:
        if file.strip().endswith(".py"):
            churn[file.strip()] = churn.get(file.strip(), 0) + 1
    return churn


def get_module_dependencies(folder_path):
    dependencies = []
    modules = set()
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(
                    full_path, folder_path).replace("\\", "/")
                modules.add(rel_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=rel_path)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                if node.module and not node.level:
                                    target = node.module.replace(
                                        ".", "/") + ".py"
                                    if target in modules:
                                        dependencies.append((rel_path, target))
                except Exception as e:
                    print(f"Failed to parse {rel_path}: {e}")
    return dependencies


def visualize_module_graph(folder_path, output_file="module_view.html"):
    locs = get_module_locs(folder_path)
    churn = get_module_churn(folder_path)
    edges = get_module_dependencies(folder_path)

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
                text=[os.path.basename(n) for n in G.nodes()],
                hovertext=node_text,
                hoverinfo='text',
                textposition='bottom center'
            )
        ],
        layout=go.Layout(
            title=dict(text="Module Dependency View (LOC + Churn)",
                       font=dict(size=20)),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)
        )
    )
    fig.write_html(output_file)
    print(f"Saved interactive module view to: {output_file}")


# Example usage:
visualize_module_graph("api", "module_view.html")
