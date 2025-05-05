import ast
import os
import networkx as nx
import matplotlib.pyplot as plt


class ClassRelationExtractor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.class_relations = []  # (child, parent)

    def visit_ClassDef(self, node):
        class_name = node.name
        for base in node.bases:
            if isinstance(base, ast.Name):  # e.g., `class Foo(Bar):`
                self.class_relations.append((class_name, base.id))
            elif isinstance(base, ast.Attribute):  # e.g., `class Foo(models.Model):`
                self.class_relations.append((class_name, base.attr))
        self.generic_visit(node)


def extract_from_folder(folder):
    all_relations = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=path)
                        extractor = ClassRelationExtractor(path)
                        extractor.visit(tree)
                        all_relations.extend(extractor.class_relations)
                    except Exception as e:
                        print(f"Failed to parse {path}: {e}")
    return all_relations


relations = extract_from_folder("api")
G = nx.DiGraph()
G.add_edges_from(relations)
plt.figure(figsize=(12, 8))
nx.draw(G, with_labels=True, node_size=1500,
        node_color="lightblue", font_size=10)
plt.title("Class Inheritance Graph")
plt.show()
