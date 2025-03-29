# src/models/robot.py
import os
import random
import math
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsColorizeEffect, QGraphicsRectItem
)
from PyQt6.QtGui import QPixmap, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QPointF

class Robot(QGraphicsPixmapItem):
    def __init__(self, x, y, identifier, current_vertex_index, parent=None):
        # Load the common robot image from the assets folder.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        image_path = os.path.join(parent_dir, "assets", "robot.png")
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        super().__init__(pixmap, parent)
        self.setPos(x, y)
        self.id = identifier
        self.current_vertex_index = current_vertex_index  # The vertex where the robot is (or will be) located.
        self.route = []  # List of QPointF waypoints.
        self.speed = 2.0  # Movement speed.
        self.selected = False
        self.waiting = False  # Flag for collision avoidance.
        # Initial status is "unassigned".
        self.status = "unassigned"  
        
        # Apply a unique random color tint to the robot image.
        self.unique_color = QColor(random.randint(0,255), random.randint(0,255), random.randint(0,255))
        effect = QGraphicsColorizeEffect()
        effect.setColor(self.unique_color)
        self.setGraphicsEffect(effect)
        
        # Add a text label to display the robot ID.
        self.text = QGraphicsTextItem(str(self.id), self)
        self.text.setDefaultTextColor(QColor("white"))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        self.text.setFont(font)
        self.text.setPos(10, 10)
        
        # Create a border as a QGraphicsRectItem child to indicate status.
        self.border = QGraphicsRectItem(self.boundingRect(), self)
        self.border.setPen(QPen(Qt.GlobalColor.darkGray, 2))
        self.border.setBrush(Qt.GlobalColor.transparent)
        
        self.update_visual_status()
    
    def update_visual_status(self):
        """Update the border's pen color based on the robot's current status."""
        if self.status == "unassigned":
            pen = QPen(Qt.GlobalColor.darkGray, 2)
        elif self.status == "task assigned":
            pen = QPen(Qt.GlobalColor.magenta, 3)
        elif self.status == "moving":
            pen = QPen(Qt.GlobalColor.black, 2)
        elif self.status == "waiting":
            pen = QPen(Qt.GlobalColor.yellow, 3)
        elif self.status == "charging":
            pen = QPen(Qt.GlobalColor.blue, 3)
        elif self.status == "task complete":
            pen = QPen(Qt.GlobalColor.green, 3)
        else:
            pen = QPen(Qt.GlobalColor.black, 2)
        self.border.setPen(pen)
    
    def setSelected(self, selected: bool):
        self.selected = selected
        self.setOpacity(0.8 if selected else 1.0)
    
    def update_position(self):
        """
        Move the robot along its route and update its status.
        When the robot has no remaining route and was previously in a task state,
        mark its task as complete and release the reservation on the destination vertex.
        """
        if self.route:
            current_pos = self.pos()
            next_point = self.route[0]
            dx = next_point.x() - current_pos.x()
            dy = next_point.y() - current_pos.y()
            distance = math.hypot(dx, dy)
            if distance < self.speed:
                self.setPos(next_point)
                self.route.pop(0)
            else:
                angle = math.atan2(dy, dx)
                new_x = current_pos.x() + self.speed * math.cos(angle)
                new_y = current_pos.y() + self.speed * math.sin(angle)
                self.setPos(new_x, new_y)
            # While there is a route, the robot is "moving".
            self.status = "moving"
        else:
            # If a task was previously assigned or the robot was moving or waiting, mark task complete.
            if self.status in ["task assigned", "moving", "waiting"]:
                self.status = "task complete"
                # Release reservation on the destination vertex.
                # Assumes that the robot's parent has an attribute 'vertex_items'
                # containing the vertices data.
                try:
                    vertex = self.parent().vertex_items[self.current_vertex_index]
                    vertex["reserved_by"] = None
                    # If there is a waiting queue, you might trigger assignment of the next robot.
                    if vertex["waiting_queue"]:
                        next_robot_id = vertex["waiting_queue"].pop(0)
                        # Here you could notify the FleetManager to assign a task to the waiting robot.
                except Exception as e:
                    # In case the parent does not have vertex_items, log or handle the exception.
                    pass
        self.update_visual_status()
