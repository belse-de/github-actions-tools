#!/usr/bin/env python3
import argparse

import yaml
import pydot
import glob
import os
from collections import deque, namedtuple
from dataclasses import dataclass, field as dc_field


@dataclass
class Config:
    base_file_name: str = "dot/gh_dependencies"
    sub_graphs: list[str] = dc_field(default_factory=list)
    include_external: bool = True
    include_scripts: bool = True


"""
MAYBE help full
flags:
    workflow:
        - call
        - dispatch
        - schedule
interesting additional output format: mermaid -> can be used in github flavored markdown
    https://mermaid.js.org/
    https://mermaidpy.vercel.app/mermaid/graph
    https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams
"""


def is_on_workflow_dispatch(gh_script):
    return True in gh_script and "workflow_dispatch" in gh_script[True]


def find_field(gh_script, field_name: str):
    field = []
    if isinstance(gh_script, dict):
        for k, v in gh_script.items():
            if k == field_name:
                field.append(v)
            field += find_field(v, field_name)
    elif isinstance(gh_script, list):
        for v in gh_script:
            field += find_field(v, field_name)
    else:
        pass
    return field


def find_uses(gh_script):
    return find_field(gh_script, "uses")


def find_run(gh_script):
    return find_field(gh_script, "run")


def find_connected_nodes_and_edges_bfs(graph, node_name: str):
    connected_nodes_up = set()
    connected_nodes_down = set()
    connected_edges = set()

    # BFS to find all UPWARD connected nodes and edges
    queue = deque([node_name])
    while queue:
        current_node = queue.popleft()
        if current_node not in connected_nodes_up:
            # print('bfs processing node:', current_node)
            connected_nodes_up.add(current_node)
            for edge in graph.edges:
                if edge.destination == current_node:
                    connected_edges.add(edge)
                    queue.append(edge.source)

    # BFS to find all DOWNWARD connected nodes and edges
    queue = deque([node_name])
    while queue:
        current_node = queue.popleft()
        if current_node not in connected_nodes_down:
            # print('bfs processing node:', current_node)
            connected_nodes_down.add(current_node)
            for edge in graph.edges:
                if edge.source == current_node:
                    connected_edges.add(edge)
                    queue.append(edge.destination)

    # Combine the connected nodes from both directions
    connected_nodes = connected_nodes_up.union(connected_nodes_down)
    return connected_nodes, connected_edges


Node = namedtuple("Node", ["name", "attributes"])
Edge = namedtuple("Edge", ["source", "destination", "attributes"])
Graph = namedtuple("Graph", ["nodes", "edges"])


def create_usage_sub_graph(graph, node_name: str):
    connected_nodes, connected_edges = find_connected_nodes_and_edges_bfs(graph, node_name)

    sub_edges = set()
    sub_nodes = set()

    for node_name in connected_nodes:
        original_nodes = [node for node in graph.nodes if node.name == node_name]  # Get the original Node object
        if len(original_nodes) == 0:
            print(f"Warning: Node '{node_name}' not found in the original graph.")
            continue
        assert len(original_nodes) > 0

        original_node = original_nodes[0]
        sub_nodes.add(original_node)

    for edge in connected_edges:
        sub_edges.add(edge)

    return Graph(sub_nodes, sub_edges)


def gh_script_usage_graph(config: Config) -> Graph:
    edges = set()
    nodes = set()

    file_path_iter = glob.glob("./.github/**/*.yaml", recursive=True)
    for file_path in file_path_iter:
        with open(file_path) as gh_file:
            node_name = ""
            node_attr = set()

            if os.path.basename(file_path) == "action.yaml":
                node_name = file_path[: -len("/action.yaml")]
                node_attr.add("action")
            else:
                node_name = file_path
                node_attr.add("workflow")

            gh_script = yaml.safe_load(gh_file)
            if is_on_workflow_dispatch(gh_script):
                node_attr.add("entry")

            node = Node(node_name, frozenset(node_attr))
            nodes.add(node)

            # print(node_name)
            uses = find_uses(gh_script)
            for v in uses:
                is_external = not v.startswith("./")
                if is_external and not config.include_external:
                    continue

                other_node_name = v.split("@")[0]  # without version string
                # print('  ', other_node_name)
                if is_external:
                    other_node_attr = set()
                    other_node_attr.add("external")

                    if other_node_name.endswith(".yaml"):
                        other_node_attr.add("workflow")
                    else:
                        other_node_attr.add("action")

                    other_node = Node(other_node_name, frozenset(other_node_attr))
                    nodes.add(other_node)

                edge = Edge(node_name, other_node_name, frozenset())
                if edge not in edges:
                    edges.add(edge)

            if config.include_scripts:
                # find all run / shell invocations
                runs = find_run(gh_script)
                for r in runs:
                    if isinstance(r, str) and len(r):
                        r = r.splitlines()
                        if len(r) == 1:
                            r = r[0].strip()
                            rs = r.split()
                            if len(rs) > 0:
                                r = rs[0]
                            r = r.strip().strip("\"").strip("'")

                            prefixes = ["./", "$GITHUB_ACTION_PATH"]
                            if any(r.startswith(prefix) for prefix in prefixes):
                                if "action" in node_attr:
                                    r = r.replace("$GITHUB_ACTION_PATH", node_name)
                                # TODO: handle working directory change
                                script_node = Node(r, frozenset({"script"}))
                                if script_node not in nodes:
                                    nodes.add(script_node)
                                scrip_edge = Edge(node_name, r, frozenset())
                                if scrip_edge not in edges:
                                    edges.add(scrip_edge)

                                print(f"found run script: {r}")
    return Graph(nodes, edges)


def graph_to_dot(
    graph: Graph, node_styles: dict[frozenset, dict[str, str]], edge_styles: dict[frozenset, dict[str, str]]
) -> pydot.Dot:
    dot_graph = pydot.Dot("gh_script_uses", graph_type="digraph")
    dot_graph.set("normalize", "true")

    for node in graph.nodes:
        node_name = '"{}"'.format(node.name)
        node_attr = node_styles[node.attributes]

        dot_node = pydot.Node(node_name, **node_attr)
        dot_graph.add_node(dot_node)

    for edge in graph.edges:
        source_name = '"{}"'.format(edge.source)
        destination_name = '"{}"'.format(edge.destination)
        edge_attr = edge_styles[edge.attributes]

        dot_edge = pydot.Edge(source_name, destination_name, **edge_attr)
        dot_graph.add_edge(dot_edge)

    return dot_graph


def write_dot_graph(dot_graph: pydot.Dot, file_name: str):
    dot_graph.write_raw(file_name + ".dot")
    dot_graph.write_png(file_name + ".png", prog="dot")


def write_graph(graph: Graph, file_name: str):
    node_styles = {
        frozenset(): {},
        frozenset({"workflow"}): {"shape": "box", "style": "filled", "fillcolor": "yellow"},
        frozenset({"workflow", "entry"}): {"shape": "box", "style": "filled", "fillcolor": "cyan"},
        frozenset({"workflow", "external"}): {"shape": "box", "style": "filled", "fillcolor": "gray"},
        frozenset({"action"}): {},
        frozenset({"action", "external"}): {"style": "filled", "fillcolor": "gray"},
        frozenset({"script"}): {"shape": "diamond", "style": "filled", "fillcolor": "green"},
    }

    edge_styles = {
        frozenset(): {},
    }

    write_dot_graph(graph_to_dot(graph, node_styles, edge_styles), file_name)


def write_subgraph(graph: Graph, node_name: str, file_name: str):
    sub_graph = create_usage_sub_graph(graph, node_name)
    write_graph(sub_graph, file_name)


def create_and_write_dependency_graphs(config: Config):
    # as subgraph file names we use the base file name with a suffix
    # e.g. "dot/gh_script_uses_vault" for the vault subgraph
    # the suffix is generated by picking the last path element of the node name
    # and appending it to the base file name
    wanted_subgraphs = [
        (node_name, f"{config.base_file_name}_{os.path.basename(node_name)}") for node_name in config.sub_graphs
    ]
    # Create the graph from GitHub workflows
    graph = gh_script_usage_graph(config)
    write_graph(graph, config.base_file_name)
    # Create a subgraph for a specific node
    for node_name, subgraph_file_name in wanted_subgraphs:
        write_subgraph(graph, node_name, subgraph_file_name)


def main():
    default_config: Config = Config()
    argument_parser = argparse.ArgumentParser(description="Create GitHub Actions dependency graphs.")
    argument_parser.add_argument(
        "--base_file_name",
        type=str,
        default=default_config.base_file_name,
        help="Base file name for the output dependency graph files.",
    )
    argument_parser.add_argument(
        "--sub-graphs",
        nargs="+",
        default=default_config.sub_graphs,
        help="List of nodes for which to create sub-graphs.",
    )
    argument_parser.add_argument(
        "--include_external",
        action=argparse.BooleanOptionalAction,
        help="Include external actions in the dependency graph.",
        default=default_config.include_external,
    )
    argument_parser.add_argument(
        "--include_scripts",
        action=argparse.BooleanOptionalAction,
        help="Include scripts in the dependency graph.",
        default=default_config.include_scripts,
    )
    args = argument_parser.parse_args()
    config: Config = Config(**vars(args))
    create_and_write_dependency_graphs(config)


if __name__ == "__main__":
    main()
