import os
import random
import math
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsColorizeEffect, QGraphicsRectItem
)
from PyQt6.QtGui import QPixmap, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QPointF

# Threshold (in pixels) to decide if the robot is "at" a vertex.
AT_VERTEX_THRESHOLD = 5

class Robot(QGraphicsPixmapItem):
    def __init__(self, x, y, identifier, current_vertex_index, vertex_items, parent=None):
        """
        x, y: starting scene coordinates.
        identifier: unique robot id.
        current_vertex_index: index of the vertex where the robot spawns.
        vertex_items: reference to the shared dictionary of vertices from NavGraph.
        """
        # Load and scale the robot image.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        image_path = os.path.join(parent_dir, "assets", "robot.png")
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        super().__init__(pixmap, parent)
        self.setPos(x, y)
        self.id = identifier
        self.current_vertex_index = current_vertex_index
        self.current_destination_index = None  # Set when a task is assigned.
        self.vertex_items = vertex_items  # Shared reference.
        
        # Reserve the starting vertex.
        self.vertex_items[self.current_vertex_index]["reserved_by"] = self.id
        
        self.route = []  # List of QPointF waypoints.
        self.speed = 2.0
        self.selected = False
        self.waiting = False
        self.status = "unassigned"
        
        # Apply a unique color tint.
        self.unique_color = QColor(random.randint(0,255), random.randint(0,255), random.randint(0,255))
        effect = QGraphicsColorizeEffect()
        effect.setColor(self.unique_color)
        self.setGraphicsEffect(effect)
        
        # Display robot ID.
        self.text = QGraphicsTextItem(str(self.id), self)
        self.text.setDefaultTextColor(QColor("white"))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        self.text.setFont(font)
        self.text.setPos(10, 10)
        
        # Border for visual status.
        self.border = QGraphicsRectItem(self.boundingRect(), self)
        self.border.setPen(QPen(Qt.GlobalColor.darkGray, 2))
        self.border.setBrush(Qt.GlobalColor.transparent)
        
        self.update_visual_status()
    
    def update_visual_status(self):
        """Update the border pen based on the robot's status."""
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
        Moves the robot along its route.
        - If the route is non-empty, the robot moves toward the next waypoint.
        - If the robot has moved beyond the AT_VERTEX_THRESHOLD from its starting vertex,
          clear that vertex's reservation.
        - When the route is empty and the robot is near the destination vertex,
          update the current vertex and reserve it.
        """
        if self.route:
            current_pos = self.pos()
            next_point = self.route[0]
            dx = next_point.x() - current_pos.x()
            dy = next_point.y() - current_pos.y()
            distance = math.hypot(dx, dy)
            
            # Move toward the next waypoint.
            if distance < self.speed:
                self.setPos(next_point)
                self.route.pop(0)
            else:
                angle = math.atan2(dy, dx)
                new_x = current_pos.x() + self.speed * math.cos(angle)
                new_y = current_pos.y() + self.speed * math.sin(angle)
                self.setPos(new_x, new_y)
            
            self.status = "moving"
            
            # Check if the robot has left its current vertex.
            vertex_pos = self.vertex_items[self.current_vertex_index]["pos"]
            if math.hypot(self.pos().x() - vertex_pos[0], self.pos().y() - vertex_pos[1]) > AT_VERTEX_THRESHOLD:
                # Clear the reservation if it was reserved by this robot.
                if self.vertex_items[self.current_vertex_index]["reserved_by"] == self.id:
                    self.vertex_items[self.current_vertex_index]["reserved_by"] = None
        else:
            # Route is empty: robot has (presumably) arrived.
            if self.current_destination_index is not None:
                dest_pos = self.vertex_items[self.current_destination_index]["pos"]
                if math.hypot(self.pos().x() - dest_pos[0], self.pos().y() - dest_pos[1]) <= AT_VERTEX_THRESHOLD:
                    # Robot has arrived at its destination.
                    self.current_vertex_index = self.current_destination_index
                    self.vertex_items[self.current_vertex_index]["reserved_by"] = self.id
            if self.status in ["task assigned", "moving", "waiting"]:
                self.status = "task complete"
        
        self.update_visual_status()
