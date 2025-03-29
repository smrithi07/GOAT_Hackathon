# src/controllers/fleet_manager.py
from PyQt6.QtCore import QPointF
from src.models.robot import Robot

class FleetManager:
    def __init__(self, scene, nav_graph):
        self.scene = scene
        self.nav_graph = nav_graph  # Instance of NavGraph.
        self.robots = []
        self.robot_counter = 1
        self.selected_robot = None

    def spawn_robot(self, vertex_index, position):
        robot = Robot(position[0], position[1], self.robot_counter, vertex_index)
        self.robot_counter += 1
        self.scene.addItem(robot)
        self.robots.append(robot)
        return robot

    def assign_task(self, robot, dest_vertex_index, vertex_items):
        # Compute route using A* from nav_graph.
        path_indices = self.nav_graph.get_shortest_path(robot.current_vertex_index, dest_vertex_index)
        if path_indices:
            route = []
            for idx in path_indices:
                pos = vertex_items[idx]["pos"]
                route.append(QPointF(pos[0], pos[1]))
            robot.route = route
            robot.current_vertex_index = dest_vertex_index
