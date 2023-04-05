import ast
import networkx as nx
from typing import List


class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, graph: nx.DiGraph, parent: str = None):
        self.graph = graph
        self.parent = parent

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            called_function = node.func.id

            # Add nodes for both the calling and called functions
            self.graph.add_node(self.parent)
            self.graph.add_node(called_function)

            # Add an edge between the calling and called functions
            self.graph.add_edge(self.parent, called_function)

        # Continue traversing the AST
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        original_parent = self.parent
        self.parent = node.name

        self.graph.add_node(self.parent)
        self.generic_visit(node)
        self.parent = original_parent


def extract_call_graph(file_path: str) -> nx.DiGraph:
    with open(file_path, "r") as f:
        source_code = f.read()
    tree = ast.parse(source_code)
    call_graph = nx.DiGraph()

    visitor = CallGraphVisitor(call_graph)
    visitor.visit(tree)

    return call_graph


if __name__ == '__main__':
    call_graph = extract_call_graph(r'C:\github\!searchGPT\searchGPT\src\main.py')
    print(call_graph)
