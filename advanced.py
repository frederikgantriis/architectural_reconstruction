import ast
import os
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go


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


def save_plotly_graph(inheritance, usage, output_file="zeeguu_class_relations.html"):
    G = nx.DiGraph()

    # Add inheritance edges
    for child, parent in inheritance:
        G.add_edge(child, parent, relation="inherits")

    # Add usage edges
    for user_class, used_classes in usage.items():
        for used_class in used_classes:
            G.add_edge(user_class, used_class, relation="uses")

    pos = nx.spring_layout(G, seed=42)

    # Create edge traces
    edge_x = []
    edge_y = []
    edge_text = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_text.append(f"{u} → {v} ({data['relation']})")

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="bottom center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='lightblue',
            size=14,
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=dict(
                            text="Class Relationships in Zeeguu API",
                            font=dict(size=20)
                        ),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False)))

    fig.write_html(output_file)
    print(f"Saved interactive graph to {output_file}")


inheritance, usage = extract_relations_from_folder("api")
save_plotly_graph(inheritance, usage, "zeeguu_class_relations.html")

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
plt.show()
plt.tight_layout()
plt.savefig("class_relations.png", dpi=300)  # Save the figure
