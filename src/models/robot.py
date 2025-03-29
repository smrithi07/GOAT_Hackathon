# src/models/robot.py
import os
import random
import math
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsColorizeEffect
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QPointF

class Robot(QGraphicsPixmapItem):
    def __init__(self, x, y, identifier, current_vertex_index, parent=None):
        # Load the common robot image from the assets folder.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        image_path = os.path.join(parent_dir, "assets", "robot.png")
        pixmap = QPixmap(image_path)
        # Scale the image to a consistent size.
        pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        super().__init__(pixmap, parent)
        self.setPos(x, y)
        self.id = identifier
        self.current_vertex_index = current_vertex_index  # Track which vertex the robot is at.
        self.route = []  # List of QPointF waypoints.
        self.speed = 2.0  # Movement speed.
        self.selected = False
        self.waiting = False  # Flag for collision avoidance.
        
        # Apply a unique random color tint to the robot image.
        self.unique_color = QColor(random.randint(0,255), random.randint(0,255), random.randint(0,255))
        effect = QGraphicsColorizeEffect()
        effect.setColor(self.unique_color)
        self.setGraphicsEffect(effect)
        
        # Add a text label to clearly display the robot ID.
        self.text = QGraphicsTextItem(str(self.id), self)
        self.text.setDefaultTextColor(QColor("white"))
        # Adjust label position as needed.
        self.text.setPos(10, 10)
    
    def setSelected(self, selected: bool):
        self.selected = selected
        # Change appearance if selected (e.g., slightly change opacity).
        self.setOpacity(0.8 if selected else 1.0)
    
    def update_position(self):
        """Move the robot along its route using a simple step-by-step approach."""
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
