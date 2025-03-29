# src/main.py
from src.gui.dashboard import FleetDashboard
from PyQt6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    window = FleetDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
