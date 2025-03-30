# src/gui/dashboard.py
import os
import sys
import math
from PyQt6.QtWidgets import (
    QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QApplication,
    QStatusBar, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QSplitter, QMessageBox
)
from PyQt6.QtGui import QColor, QFont, QBrush, QPen
from PyQt6.QtCore import Qt, QTimer, QPointF
from src.models.nav_graphs import NavGraph
from src.controllers.fleet_manager import FleetManager
from src.controllers.tarffic_manager import TrafficManager

class FleetDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fleet Management System")
        self.setGeometry(100, 100, 1200, 700)
        
        # Main widget and layout.
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        
        # Left panel: graphics view for the graph.
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#f0f8ff")))  # AliceBlue background
        self.view = QGraphicsView(self.scene, self)
        self.view.setMinimumWidth(800)
        
        # Right panel: table to display robot statuses.
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels(["Robot ID", "Current Vertex", "Status", "Next WP"])
        self.status_table.setMinimumWidth(350)
        
        # Use a splitter for adjustable panels.
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.status_table)
        self.main_layout.addWidget(self.splitter)
        
        # Create status bar for notifications.
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Load navigation graph.
        self.nav_graph = NavGraph("nav_graph_2.json")
        self.vertex_items = self.nav_graph.vertices
        
        self.draw_vertices()
        self.draw_lanes()
        
        # Initialize managers.
        self.fleet_manager = FleetManager(self.scene, self.nav_graph)
        self.traffic_manager = TrafficManager()
        
        self.selected_robot = None
        self.initTimer()
    
    def draw_vertices(self):
        """Draw vertices with labels and tooltips."""
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
            label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            label.setPos(-20, -30)
            
            self.graphics_vertices[index] = {"item": ellipse, "pos": (x, y), "name": name}
            ellipse.mousePressEvent = lambda event, idx=index: self.vertexClicked(idx)
    
    def draw_lanes(self):
        """Draw lanes connecting vertices."""
        pen = QPen(Qt.GlobalColor.black, 2)
        for edge in self.nav_graph.lanes:
            start_index, end_index = edge
            start_pos = self.vertex_items[start_index]["pos"]
            end_pos = self.vertex_items[end_index]["pos"]
            line = QGraphicsLineItem(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
            line.setPen(pen)
            self.scene.addItem(line)
    
    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateRobots)
        self.timer.start(50)
    
    def updateRobots(self):
        """Update robot positions, collisions, table, and vertex visuals."""
        for robot in self.fleet_manager.robots:
            robot.update_position()
        self.traffic_manager.check_collisions(self.fleet_manager.robots, self.vertex_items, self.nav_graph)
        
        self.update_status_table()
        
        # Update vertex visuals based on reservations.
        for index, data in self.graphics_vertices.items():
            vertex = self.vertex_items[index]
            if vertex["reserved_by"] is not None or vertex["waiting_queue"]:
                data["item"].setBrush(QBrush(QColor("red")))
                waiting_info = ", ".join(str(x) for x in vertex["waiting_queue"]) if vertex["waiting_queue"] else "None"
                data["item"].setToolTip(f"Vertex '{data['name']}' occupied by Robot {vertex['reserved_by']}.\nWaiting: {waiting_info}")
            else:
                if vertex["is_charger"]:
                    data["item"].setBrush(QBrush(QColor("green")))
                else:
                    data["item"].setBrush(QBrush(QColor("cyan")))
                data["item"].setToolTip(f"Vertex '{data['name']}' is free.")
        
        if self.traffic_manager.warnings:
            self.status_bar.showMessage("Warnings: " + " | ".join(self.traffic_manager.warnings))
        else:
            self.status_bar.clearMessage()
    
    def update_status_table(self):
        robots = self.fleet_manager.robots
        self.status_table.setRowCount(len(robots))
        for i, robot in enumerate(robots):
            self.status_table.setItem(i, 0, QTableWidgetItem(str(robot.id)))
            self.status_table.setItem(i, 1, QTableWidgetItem(str(robot.current_vertex_index)))
            self.status_table.setItem(i, 2, QTableWidgetItem(robot.status))
            if robot.route:
                wp = robot.route[0]
                self.status_table.setItem(i, 3, QTableWidgetItem(f"({wp.x():.1f}, {wp.y():.1f})"))
            else:
                self.status_table.setItem(i, 3, QTableWidgetItem("None"))
    
    def vertexClicked(self, vertex_index):
        """On vertex click, if reserved, show warning pop-up; otherwise assign task or spawn robot."""
        vertex = self.vertex_items[vertex_index]
        if vertex["reserved_by"] is not None:
            QMessageBox.warning(self, "Vertex Reserved",
                                f"Vertex '{vertex['name']}' is already reserved by Robot {vertex['reserved_by']}.")
            if self.selected_robot is not None:
                if self.selected_robot.id not in vertex["waiting_queue"]:
                    vertex["waiting_queue"].append(self.selected_robot.id)
                self.selected_robot.status = "waiting"
                self.selected_robot.setSelected(False)
                self.selected_robot = None
            return
        
        if self.selected_robot:
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
