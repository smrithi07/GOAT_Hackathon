# src/controllers/fleet_manager.py
from PyQt6.QtCore import QPointF
from src.models.robot import Robot
from src.utils.helper import log_event

class FleetManager:
    def __init__(self, scene, nav_graph):
        self.scene = scene
        self.nav_graph = nav_graph  # Instance of NavGraph.
        self.robots = []
        self.robot_counter = 1
        self.selected_robot = None

    def spawn_robot(self, vertex_index, position):
        # Spawn a new robot with initial status "unassigned".
        robot = Robot(position[0], position[1], self.robot_counter, vertex_index)
        self.robot_counter += 1
        self.scene.addItem(robot)
        self.robots.append(robot)
        log_event(f"Spawned robot {robot.id} at {position} on vertex {vertex_index}", "info")
        return robot

    def assign_task(self, robot, dest_vertex_index, vertex_items):
        vertex = vertex_items[dest_vertex_index]
        # Check if destination is reserved.
        if vertex.get("reserved_by") is not None:
            # Add robot to waiting queue.
            vertex["waiting_queue"].append(robot.id)
            # Log event and update robot status to "waiting".
            log_event(f"Robot {robot.id} waiting for vertex {dest_vertex_index} (already reserved by Robot {vertex['reserved_by']})", "warning")
            robot.status = "waiting"
            return  # Do not assign a task immediately.
        else:
            # Reserve the vertex.
            vertex["reserved_by"] = robot.id
            robot.status = "task assigned"
            log_event(f"Robot {robot.id} assigned task from vertex {robot.current_vertex_index} to {dest_vertex_index}", "info")
            path_indices = self.nav_graph.get_shortest_path(robot.current_vertex_index, dest_vertex_index)
            if path_indices:
                log_event(f"Robot {robot.id} path chosen: {path_indices}", "debug")
                route = []
                for idx in path_indices:
                    pos = vertex_items[idx]["pos"]
                    route.append(QPointF(pos[0], pos[1]))
                robot.route = route
                robot.current_vertex_index = dest_vertex_index
