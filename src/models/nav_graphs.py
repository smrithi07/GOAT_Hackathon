import json
import os
import math
import networkx as nx

class NavGraph:
    def __init__(self, json_filename):
        self.graph = nx.Graph()
        self.vertices = {}  # Dict: vertex_index -> {"pos": (x, y), "name": str, "is_charger": bool}
        self.lanes = []     # List of (start_index, end_index) tuples
        self.load_graph(json_filename)
    
    def load_graph(self, json_filename):
        # Build the file path: assumes data folder is one level up from src.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        data_path = os.path.join(parent_dir, "data", json_filename)
        
        with open(data_path, "r") as f:
            nav_data = json.load(f)
        
        # Check if the JSON has a "levels" key.
        levels = nav_data.get("levels", {})
        if levels:
            # Generalize: pick the first level key (e.g., "level1", "l0", etc.)
            level_key = next(iter(levels))
            level_data = levels[level_key]
        else:
            level_data = nav_data
        
        vertices_data = level_data.get("vertices", [])
        lanes_data = level_data.get("lanes", [])
        
        # Define scaling factors and offsets to convert raw coordinates to scene coordinates.
        scale = 50
        offset_x = 400
        offset_y = 300
        
        # Process vertices.
        for index, vertex in enumerate(vertices_data):
            x_val, y_val, attrs = vertex
            name = attrs.get("name", f"V{index}")
            is_charger = attrs.get("is_charger", False)
            x = (x_val * scale) + offset_x
            y = (y_val * scale) + offset_y
            self.vertices[index] = {"pos": (x, y), "name": name, "is_charger": is_charger}
            self.graph.add_node(index, pos=(x, y))
        
        # Process lanes.
        for lane in lanes_data:
            start_index, end_index, _ = lane
            if start_index in self.vertices and end_index in self.vertices:
                pos1 = self.vertices[start_index]["pos"]
                pos2 = self.vertices[end_index]["pos"]
                weight = math.hypot(pos2[0] - pos1[0], pos2[1] - pos1[1])
                self.graph.add_edge(start_index, end_index, weight=weight)
                self.lanes.append((start_index, end_index))
    
    def get_shortest_path(self, start_index, dest_index):
        # Use A* algorithm with Euclidean distance as heuristic.
        def heuristic(u, v):
            pos_u = self.graph.nodes[u]["pos"]
            pos_v = self.graph.nodes[v]["pos"]
            return math.hypot(pos_v[0] - pos_u[0], pos_v[1] - pos_u[1])
        try:
            path = nx.astar_path(self.graph, start_index, dest_index, heuristic=heuristic, weight='weight')
            return path
        except nx.NetworkXNoPath:
            print("No path found between", start_index, "and", dest_index)
            return []
