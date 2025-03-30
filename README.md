Fleet Management System with Traffic Negotiation
A Python-based fleet management system for multi-robot navigation through a dynamic environment. This system features:

Graphical Visualization
Interactive display of the environment using a navigation graph with vertices (locations) and lanes (connections).

Robot Spawning & Task Assignment
Dynamically spawn robots by clicking on vertices and assign navigation tasks.

Real-Time Traffic Negotiation & Collision Avoidance
Robots dynamically detect collisions, wait at vertices if blocked, and re-plan their routes as needed.

Dynamic Vertex Reservations
Vertices are reserved when occupied and released when robots move away, with visual indicators (colors and tooltips).

Detailed Logging
The system logs robot actions, path choices, waiting conditions, and task completions into a log file.
