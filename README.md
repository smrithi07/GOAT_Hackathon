**Fleet Management System with Traffic Negotiation**
A Python-based fleet management system for multi-robot navigation through a dynamic environment. 

**Features**
**Interactive GUI:**
Built using PyQt6, the system provides a dashboard with a visual environment and a side table displaying robot statuses.

**Dynamic Task Assignment:**
Click on vertices to spawn robots or assign tasks. Reserved vertices display warnings via color changes (red when occupied) and tooltips.

**Collision Avoidance & Re-Planning:**
Real-time detection of collisions and re-planning of robot routes based on occupancy.

**Real-Time Updates:**
A QTimer continuously updates robot positions, vertex reservations, and UI elements.

**Detailed Logging:**
All significant events are logged in fleet_logs.txt for debugging and demonstration



---

## Usage

### Running the Application

1. **Activate the Virtual Environment**  
   If you haven't already, activate your virtual environment:
   ```bash
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Start the System**  
   Launch the fleet management dashboard by running:
   ```bash
   python src/main.py
   ```
![image](https://github.com/user-attachments/assets/5dbbe822-5ec9-488d-8e9e-f0f702f450bd)

### Interacting with the Dashboard

Once the application is running, you will see a split-screen interface:

- **Left Panel: Graphical Environment**  
  - **Vertices (Nodes):**  
    - Each vertex is represented as a colored circle:
      - **Green**: Charger vertices.
      - **Cyan**: Regular vertices.
      - **Red**: Vertices currently reserved or blocked.
    - **Tooltips:**  
      Hovering over a vertex shows details about its occupancy (which robot has reserved it and any waiting robots).
  - **Lanes:**  
    - Lines connecting the vertices represent possible paths for robot movement.
  
- **Right Panel: Status Table**  
  - Displays a list of all active robots with the following information:
    - **Robot ID:** Unique identifier for each robot.
    - **Current Vertex:** The vertex index where the robot is currently located.
    - **Status:** The robot’s current status (e.g., "unassigned", "task assigned", "moving", "waiting", "task complete").
    - **Next WP:** The next waypoint coordinates if the robot is en route.

- **Status Bar:**  
  - The status bar at the bottom displays real-time warnings and notifications (e.g., collision warnings, reserved vertex alerts).

### Spawning Robots and Assigning Tasks

1. **Spawning a Robot:**  
   - Click on any vertex in the left panel.
   - A new robot is spawned at the clicked vertex.
   - The robot reserves that vertex, and its details are added to the status table.

2. **Assigning a Task to a Robot:**  
   - Click on a robot to select it (the robot will be highlighted).
   - Click on a different vertex to assign that vertex as the robot’s destination.
   - The robot computes a path (displayed in the logs) and starts moving along the route.
   - If the destination vertex is already reserved, a pop-up warning appears and the robot is added to the waiting queue for that vertex.
   - The status table updates in real time to reflect changes (e.g., status changing from "task assigned" to "moving" to "task complete").

### Real-Time Behavior

- **Dynamic Reservations:**  
  - As a robot moves away from its starting vertex, the reservation for that vertex is cleared and the vertex reverts to its default color.
  - When the robot arrives at a new vertex (within a specified threshold), it reserves that vertex, updating its color to indicate occupancy.

- **Collision Avoidance:**  
  - If a moving robot encounters a vertex that is occupied by another robot, it will wait (status changes to "waiting") until the vertex is free.
  - Warnings about waiting or collisions are displayed in the status bar.

- **Logging:**  
  - All events (robot spawning, task assignments, collisions, and re-planning) are logged in `fleet_logs.txt` for debugging and review.

![image](https://github.com/user-attachments/assets/cd171350-28bd-46cf-b871-04af6bfe2753)

![image](https://github.com/user-attachments/assets/ffad7818-4b4b-40fd-942f-9ae2e45ba08e)




