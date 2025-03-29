import math

class TrafficManager:
    def __init__(self, default_speed=2.0, collision_threshold=20, angle_threshold=0.5):
        """
        default_speed: Normal movement speed.
        collision_threshold: Minimum allowed distance (in pixels) between robots.
        angle_threshold: Angular threshold (in radians) to consider a robot 'in front'.
        """
        self.default_speed = default_speed
        self.collision_threshold = collision_threshold
        self.angle_threshold = angle_threshold

    def compute_remaining_distance(self, robot):
        """
        Computes the remaining distance along the robot's route.
        If no route, returns 0.
        """
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

    def check_collisions(self, robots):
        """
        For every pair of robots, if they're too close and one is directly ahead (within the angle threshold)
        then the robot with lower priority (based on remaining route distance, then ID) is paused.
        Additionally, if a robot is selected (i.e., the user intends to move it), then collision checks are skipped
        for that pair so that user commands can override the avoidance.
        """
        # Reset speeds and waiting flag.
        for robot in robots:
            robot.speed = self.default_speed
            robot.waiting = False

        num_robots = len(robots)
        for i in range(num_robots):
            r1 = robots[i]
            for j in range(i + 1, num_robots):
                r2 = robots[j]
                
                # If either robot is selected, skip collision check for this pair.
                if r1.selected or r2.selected:
                    continue

                vec_x = r2.pos().x() - r1.pos().x()
                vec_y = r2.pos().y() - r1.pos().y()
                distance = math.hypot(vec_x, vec_y)
                if distance >= self.collision_threshold:
                    continue

                # Determine moving direction for r1 if available.
                if r1.route:
                    current_pos = r1.pos()
                    next_wp = r1.route[0]
                    dx = next_wp.x() - current_pos.x()
                    dy = next_wp.y() - current_pos.y()
                    norm = math.hypot(dx, dy)
                    if norm == 0:
                        r1_dir = None
                    else:
                        r1_dir = (dx / norm, dy / norm)
                else:
                    r1_dir = None

                if r1_dir is not None:
                    dot = (vec_x * r1_dir[0] + vec_y * r1_dir[1])
                    if dot > 0:
                        # Clamp dot/distance to [-1, 1] to avoid domain errors in acos.
                        val = dot / distance
                        val = max(-1.0, min(1.0, val))
                        angle = math.acos(val)
                        if angle < self.angle_threshold:
                            r1_remaining = self.compute_remaining_distance(r1)
                            r2_remaining = self.compute_remaining_distance(r2)
                            if r1_remaining > r2_remaining:
                                r1.speed = 0
                                r1.waiting = True
                            elif r2_remaining > r1_remaining:
                                r2.speed = 0
                                r2.waiting = True
                            else:
                                if r1.id > r2.id:
                                    r1.speed = 0
                                    r1.waiting = True
                                else:
                                    r2.speed = 0
                                    r2.waiting = True
                else:
                    # Fallback: if r1 has no direction, use a simple rule.
                    if r1.id > r2.id:
                        r1.speed = 0
                        r1.waiting = True
                    else:
                        r2.speed = 0
                        r2.waiting = True
