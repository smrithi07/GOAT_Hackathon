# src/controllers/traffic_manager.py
import math
from PyQt6.QtCore import QPointF
from src.utils.helper import log_event

class TrafficManager:
    def __init__(self, default_speed=2.0, collision_threshold=20, release_margin=10, angle_threshold=0.5):
        """
        default_speed: Normal movement speed for robots.
        collision_threshold: Minimum allowed distance (in pixels) between robots.
        release_margin: Additional margin beyond collision_threshold before releasing waiting state.
        angle_threshold: Angular threshold (in radians) to determine if one robot is ahead.
        """
        self.default_speed = default_speed
        self.collision_threshold = collision_threshold
        self.release_margin = release_margin
        self.angle_threshold = angle_threshold
        self.warnings = []  # This list will hold instructive warning messages.

    def compute_remaining_distance(self, robot):
        """Compute the remaining distance along the robot's route."""
        if not robot.route:
            return 0
        current_pos = robot.pos()
        total = 0
        prev = current_pos
        for _, point in robot.route:
            dx = point.x() - prev.x()
            dy = point.y() - prev.y()
            total += math.hypot(dx, dy)
            prev = point
        return total

    def replan_route(self, robot, vertex_items, nav_graph):
        """
        Recalculate an alternative route for a robot (stub).
        In a full implementation, you'd incorporate congestion data into the cost function.
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
                new_route.append((idx, QPointF(pos[0], pos[1])))
            robot.route = new_route
        else:
            log_event(f"Robot {robot.id} could not replan route to {dest_index}.", "error")

    def check_collisions(self, robots, vertex_items=None, nav_graph=None):
        """
        Check for collisions among robots. If two robots come too close (i.e. distance < collision_threshold),
        instruct the user to move one of them to clear the blockage.
        If the distance exceeds (collision_threshold + release_margin), the waiting state is released.
        All instructive warning messages are appended to self.warnings.
        """
        self.warnings.clear()
        num_robots = len(robots)
        # Reset speeds, waiting flags, and update status.
        for robot in robots:
            if not robot.waiting:
                robot.speed = self.default_speed
            if robot.route:
                robot.status = "moving"
            else:
                if robot.status in ["task assigned", "moving", "waiting"]:
                    robot.status = "task complete"
            robot.update_visual_status()

        for i in range(num_robots):
            r1 = robots[i]
            for j in range(i + 1, num_robots):
                r2 = robots[j]
                if r1.selected or r2.selected:
                    continue
                vec_x = r2.pos().x() - r1.pos().x()
                vec_y = r2.pos().y() - r1.pos().y()
                distance = math.hypot(vec_x, vec_y)
                if distance < self.collision_threshold:
                    # Append instructive warnings.
                    msg1 = f"Move Robot {r1.id} to clear blockage (blocked by Robot {r2.id})"
                    msg2 = f"Move Robot {r2.id} to clear blockage (blocked by Robot {r1.id})"
                    if msg1 not in self.warnings:
                        self.warnings.append(msg1)
                    if msg2 not in self.warnings:
                        self.warnings.append(msg2)
                    # Determine which robot should wait based on remaining route distance.
                    r1_remaining = self.compute_remaining_distance(r1)
                    r2_remaining = self.compute_remaining_distance(r2)
                    if r1_remaining > r2_remaining:
                        r1.speed = 0
                        r1.waiting = True
                        r1.status = "waiting"
                    else:
                        r2.speed = 0
                        r2.waiting = True
                        r2.status = "waiting"
                else:
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
