# src/controllers/traffic_manager.py
import math
from PyQt6.QtCore import QPointF
from src.utils.helper import log_event

class TrafficManager:
    def __init__(self, default_speed=2.0, collision_threshold=20, release_margin=10, angle_threshold=0.5):
        """
        default_speed: Normal movement speed for robots.
        collision_threshold: Minimum allowed distance (in pixels) between robots.
        release_margin: Additional margin above threshold to release waiting state.
        angle_threshold: Angular threshold (in radians) to determine if one robot is ahead.
        """
        self.default_speed = default_speed
        self.collision_threshold = collision_threshold
        self.release_margin = release_margin  # Hysteresis margin to clear waiting
        self.angle_threshold = angle_threshold
        self.warnings = []  # For UI notifications

    def compute_remaining_distance(self, robot):
        """Compute the remaining distance along the robot's route."""
        if not robot.route:
            return 0
        current_pos = robot.pos()
        total = 0
        prev = current_pos
        for point in robot.route:
            dx = point.x() - prev.x()
            dy = point.y() - prev.y()
            total += math.hypot(dx, dy)
            prev = point
        return total

    def replan_route(self, robot, vertex_items, nav_graph):
        """
        Recalculate an alternative route for a robot to avoid reserved vertices or congested lanes.
        This function assumes the robot has a property 'current_destination_index'.
        """
        if not hasattr(robot, "current_destination_index") or robot.current_destination_index is None:
            log_event(f"Robot {robot.id} has no destination to replan.", "warning")
            return
        dest_index = robot.current_destination_index
        new_path = nav_graph.get_shortest_path(robot.current_vertex_index, dest_index)
        if new_path:
            log_event(f"Robot {robot.id} replanned route: {new_path}", "debug")
            new_route = []
            for idx in new_path:
                pos = vertex_items[idx]["pos"]
                new_route.append(QPointF(pos[0], pos[1]))
            robot.route = new_route
        else:
            log_event(f"Robot {robot.id} could not replan route to {dest_index}.", "error")

    def check_collisions(self, robots, vertex_items=None, nav_graph=None):
        """
        For each pair of robots within collision distance:
          - If the distance is below the collision threshold, decide which robot should wait.
          - The waiting robot remains stopped until the distance exceeds (collision_threshold + release_margin).
          - Also, if a destination is reserved, trigger re-planning.
          - Warning messages are collected for UI display.
        """
        # Clear previous warnings.
        self.warnings.clear()

        # Reset speed for all robots if they are not in a waiting state.
        for robot in robots:
            # If already waiting and still too close, do not override.
            if not robot.waiting:
                robot.speed = self.default_speed
            # Tentatively, if route exists, assume moving.
            if robot.route:
                robot.status = "moving"
            else:
                if robot.status in ["task assigned", "moving", "waiting"]:
                    robot.status = "task complete"
            robot.update_visual_status()

        num_robots = len(robots)
        for i in range(num_robots):
            r1 = robots[i]
            for j in range(i + 1, num_robots):
                r2 = robots[j]
                # Skip collision check if either robot is selected (user override).
                if r1.selected or r2.selected:
                    continue

                vec_x = r2.pos().x() - r1.pos().x()
                vec_y = r2.pos().y() - r1.pos().y()
                distance = math.hypot(vec_x, vec_y)

                # Check if we are in collision zone.
                if distance < self.collision_threshold:
                    # Check for reserved destination re-planning if applicable.
                    if vertex_items is not None and nav_graph is not None:
                        if hasattr(r1, "current_destination_index") and r1.current_destination_index is not None:
                            vertex_r1 = vertex_items[r1.current_destination_index]
                            if vertex_r1["reserved_by"] is not None and vertex_r1["reserved_by"] != r1.id:
                                self.replan_route(r1, vertex_items, nav_graph)
                        if hasattr(r2, "current_destination_index") and r2.current_destination_index is not None:
                            vertex_r2 = vertex_items[r2.current_destination_index]
                            if vertex_r2["reserved_by"] is not None and vertex_r2["reserved_by"] != r2.id:
                                self.replan_route(r2, vertex_items, nav_graph)

                    # Determine moving direction for r1.
                    if r1.route:
                        current_pos = r1.pos()
                        next_wp = r1.route[0]
                        dx = next_wp.x() - current_pos.x()
                        dy = next_wp.y() - current_pos.y()
                        norm = math.hypot(dx, dy)
                        r1_dir = (dx / norm, dy / norm) if norm != 0 else None
                    else:
                        r1_dir = None

                    if r1_dir is not None:
                        dot = (vec_x * r1_dir[0] + vec_y * r1_dir[1])
                        if dot > 0:
                            val = dot / distance
                            val = max(-1.0, min(1.0, val))  # Clamp to [-1,1]
                            angle = math.acos(val)
                            if angle < self.angle_threshold:
                                r1_remaining = self.compute_remaining_distance(r1)
                                r2_remaining = self.compute_remaining_distance(r2)
                                # Determine which robot should wait.
                                if r1_remaining > r2_remaining:
                                    # r1 should wait.
                                    r1.speed = 0
                                    r1.waiting = True
                                    r1.status = "waiting"
                                    msg = f"Robot {r1.id} waiting (collision with Robot {r2.id})"
                                    log_event(msg, "warning")
                                    if msg not in self.warnings:
                                        self.warnings.append(msg)
                                elif r2_remaining > r1_remaining:
                                    r2.speed = 0
                                    r2.waiting = True
                                    r2.status = "waiting"
                                    msg = f"Robot {r2.id} waiting (collision with Robot {r1.id})"
                                    log_event(msg, "warning")
                                    if msg not in self.warnings:
                                        self.warnings.append(msg)
                                else:
                                    if r1.id > r2.id:
                                        r1.speed = 0
                                        r1.waiting = True
                                        r1.status = "waiting"
                                        msg = f"Robot {r1.id} waiting (tie-breaker with Robot {r2.id})"
                                        log_event(msg, "warning")
                                        if msg not in self.warnings:
                                            self.warnings.append(msg)
                                    else:
                                        r2.speed = 0
                                        r2.waiting = True
                                        r2.status = "waiting"
                                        msg = f"Robot {r2.id} waiting (tie-breaker with Robot {r1.id})"
                                        log_event(msg, "warning")
                                        if msg not in self.warnings:
                                            self.warnings.append(msg)
                    else:
                        # Fallback if no moving direction.
                        if r1.id > r2.id:
                            r1.speed = 0
                            r1.waiting = True
                            r1.status = "waiting"
                            msg = f"Robot {r1.id} waiting (fallback with Robot {r2.id})"
                            log_event(msg, "warning")
                            if msg not in self.warnings:
                                self.warnings.append(msg)
                        else:
                            r2.speed = 0
                            r2.waiting = True
                            r2.status = "waiting"
                            msg = f"Robot {r2.id} waiting (fallback with Robot {r1.id})"
                            log_event(msg, "warning")
                            if msg not in self.warnings:
                                self.warnings.append(msg)
                else:
                    # If the distance is greater than the threshold plus margin,
                    # release waiting state.
                    if distance > (self.collision_threshold + self.release_margin):
                        if r1.waiting:
                            r1.waiting = False
                            r1.speed = self.default_speed
                            if r1.status == "waiting":
                                r1.status = "moving"
                        if r2.waiting:
                            r2.waiting = False
                            r2.speed = self.default_speed
                            if r2.status == "waiting":
                                r2.status = "moving"
                r1.update_visual_status()
                r2.update_visual_status()
