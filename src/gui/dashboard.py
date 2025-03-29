# src/gui/fleet_gui.py
import os
import sys
import math
from PyQt6.QtGui import QBrush, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor
from src.models.nav_graphs import NavGraph
from src.controllers.fleet_manager import FleetManager
from src.controllers.tarffic_manager import TrafficManager

# ----------------------
# A simple Robot representation as a red circle.
# ----------------------
class RobotItem(QGraphicsEllipseItem):
    def __init__(self, x, y, identifier, current_vertex_index, parent=None):
        # Draw robot as a red circle.
        radius = 8
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent)
        self.setPos(x, y)
        self.id = identifier
        self.current_vertex_index = current_vertex_index
        self.route = []  # List of QPointF waypoints.
        self.speed = 2.0
        self.selected = False

        self.setBrush(QBrush(QColor("red")))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        # Add a text label for the robot ID.
        self.text = QGraphicsTextItem(str(self.id), self)
        self.text.setDefaultTextColor(QColor("white"))
        self.text.setPos(-radius/2, -radius/2)

    def setSelected(self, selected: bool):
        self.selected = selected
        # Change appearance if selected (e.g., change pen width).
        if selected:
            self.setPen(QPen(Qt.GlobalColor.yellow, 3))
        else:
            self.setPen(QPen(Qt.GlobalColor.black, 2))

    def mousePressEvent(self, event):
        main_window = self.scene().views()[0].window()
        if hasattr(main_window, "robotClicked"):
            main_window.robotClicked(self)
        super().mousePressEvent(event)

    def update_position(self):
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

# ----------------------
# Main FleetDashboard
# ----------------------
class FleetDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fleet Management System")
        self.setGeometry(100, 100, 800, 600)
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)
        
        # Load navigation graph using our NavGraph class.
        self.nav_graph = NavGraph("nav_graph_3.json")
        self.vertex_items = self.nav_graph.vertices  # Dict: index -> {"pos": (x,y), "name": ..., "is_charger": ...}
        
        # Draw vertices and lanes.
        self.draw_vertices()
        self.draw_lanes()
        
        # Initialize managers.
        self.fleet_manager = FleetManager(self.scene, self.nav_graph)
        self.traffic_manager = TrafficManager()
        
        self.selected_robot = None
        
        self.initTimer()
    
    def draw_vertices(self):
        """Draw vertices based on the nav graph data."""
        self.graphics_vertices = {}
        for index, data in self.vertex_items.items():
            x, y = data["pos"]
            name = data["name"]
            is_charger = data["is_charger"]
            color = QColor("green") if is_charger else QColor("cyan")
            
            ellipse = QGraphicsEllipseItem(-10, -10, 20, 20)
            ellipse.setPos(x, y)
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(Qt.GlobalColor.black))
            ellipse.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
            self.scene.addItem(ellipse)
            
            label = QGraphicsTextItem(name, ellipse)
            label.setDefaultTextColor(Qt.GlobalColor.black)
            label.setPos(-10, -25)
            
            self.graphics_vertices[index] = {"item": ellipse, "pos": (x, y), "name": name}
            
            # Connect mouse click: use a lambda capturing the vertex index.
            ellipse.mousePressEvent = lambda event, idx=index: self.vertexClicked(idx)
    
    def draw_lanes(self):
        """Draw lanes as lines connecting vertices."""
        pen = QPen(Qt.GlobalColor.black, 2)
        for edge in self.nav_graph.lanes:
            start_index, end_index = edge
            start_pos = self.vertex_items[start_index]["pos"]
            end_pos = self.vertex_items[end_index]["pos"]
            line = QGraphicsLineItem(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
            line.setPen(pen)
            self.scene.addItem(line)
    
    def initTimer(self):
        """Initialize a QTimer to update robot positions."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateRobots)
        self.timer.start(50)
    
    def updateRobots(self):
        """Update positions of all robots and check for collisions."""
        for robot in self.fleet_manager.robots:
            robot.update_position()
        self.traffic_manager.check_collisions(self.fleet_manager.robots)
    
    def vertexClicked(self, vertex_index):
        """If a robot is selected, assign it a task; otherwise, spawn a new robot."""
        if self.selected_robot:
            # Assign task using A* path planning.
            self.fleet_manager.assign_task(self.selected_robot, vertex_index, self.vertex_items)
            self.selected_robot.setSelected(False)
            self.selected_robot = None
        else:
            pos = self.vertex_items[vertex_index]["pos"]
            robot = self.fleet_manager.spawn_robot(vertex_index, pos)
            print(f"Spawned robot {robot.id} at {QPointF(pos[0], pos[1])}")
            robot.mousePressEvent = lambda event, r=robot: self.robotClicked(r)
    
    def robotClicked(self, robot):
        if self.selected_robot:
            self.selected_robot.setSelected(False)
        self.selected_robot = robot
        robot.setSelected(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FleetDashboard()
    window.show()
    sys.exit(app.exec())
