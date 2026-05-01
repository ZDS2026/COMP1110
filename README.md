Overview  
This project simulates restaurant seating and queue management under different strategies.  
It compares how different table allocation policies affect:  
    Waiting time  
    Queue length   
    Table utilization  
    Service efficiency   
The simulation is implemented as a Python GUI application (Tkinter) with built-in visualization.  

Objectives  
    Compare two seating strategies (Mode 1 vs Mode 2)  
    Evaluate performance under identical customer demand  
    Analyze the impact of table configuration  
    Provide insights for restaurant operation optimization  
  
Simulation Mode 1: Single Queue + Flexible Table Allocation    
One common queue for all customers    
First-Come-First-Served (FCFS)    
Any suitable table can be used    

✔ Flexible    
✖ May cause seat waste    

Simulation Mode 2: Size-Based Queues + Dedicated Tables    
Customers are divided into 3 queues:    
1–2 people → 2-seat tables    
3–4 people → 4-seat tables    
5–6 people → 6-seat tables    
Each queue is served only by its corresponding table type    
No table sharing or reassignment    

✔ Better size matching    
✖ Less flexible    

📂 Input Format    
The program uses a CSV file:    
arrival_time,group_size,dining_time    
12.5,2,30    
15.2,4,65    
Fields:    
arrival_time — time of arrival (minutes)    
group_size — number of customers (1–6)    
dining_time — duration of stay    

Methodology    
The system uses a discrete-time simulation:    
Time progresses step-by-step (1 minute)    
At each step:    
Add new arrivals    
Release finished tables    
Update queues    
Assign tables    


Output Metrics    
Total / served / unserved groups    
Average waiting time    
Maximum waiting time    
Table utilization    
Queue length over time    
Waiting time by group size    

Visualization    
The GUI includes:    
Bar chart comparison (Mode 1 vs Mode 2)    
Queue length over time    
Summary tables    
All charts are generated dynamically from simulation results.    

How to Run    
Requirements    
Python 3.x    
Run the program    
python restaurant_simulation.py    
Steps    
Load a CSV file    
Adjust table configuration    
Click Run Both Modes    
View results and charts    
