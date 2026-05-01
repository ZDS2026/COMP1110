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



