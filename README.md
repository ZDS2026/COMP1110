🍽️ Restaurant Simulation Comparison Tool
📌 Overview

This project is a restaurant queueing simulation tool built with Python and Tkinter.
It models customer arrivals, table allocation, and waiting queues, and compares two different seating strategies.

The goal is to analyze how different operational policies affect:

Waiting time
Queue length
Table utilization
Service efficiency
⚙️ Features
📊 Compare two seating modes:
Mode 1: Single queue with flexible table usage
Mode 2: Size-based queues with dedicated table types
📂 Load real or simulated customer data via CSV
📈 Visualize results:
Queue length over time
Performance comparison charts
📉 Output key metrics:
Average waiting time
Maximum waiting time
Served / unserved customers
Table utilization
🖥️ Interactive GUI with zoom and scrolling support
🧠 Simulation Modes
Mode 1: Fixed Tables (Single Queue)
All customers join one queue
First-come-first-served (FCFS)
Any suitable table can be used
More flexible but may waste seats
Mode 2: Size-Based Queues
Customers are divided into 3 queues:
1–2 people → 2-seat tables
3–4 people → 4-seat tables
5–6 people → 6-seat tables
Each queue uses only its corresponding table type
Reduces seat mismatch but less flexible
📂 Input Format (CSV)

The program requires a CSV file with the following columns:

arrival_time,group_size,dining_time

Example:

12.5,2,30
15.0,4,60
20.2,1,25
▶️ How to Run
Install Python (3.x recommended)
Run the program:
python sim_clean_english_comments.py
In the GUI:
Set simulation parameters
Load CSV file
Click Run Both Modes
📊 Output

The program provides:

Text summary for each mode
Comparison charts
Queue length over time visualization

You can also export results to CSV.

🎯 Purpose

This project is designed for:

Simulation and modeling coursework
Queueing system analysis
Understanding trade-offs in resource allocation
📌 Notes
The simulation uses a discrete-time approach
Customers are modeled as groups (1–6 people)
Both modes use the same input data for fair comparison
