import csv
import random
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from collections import deque, Counter


class Group:
    def __init__(self, gid, arrival_time, group_size, dining_time):
        self.gid = gid
        self.arrival_time = arrival_time
        self.group_size = group_size
        self.dining_time = dining_time


class TableUnit:
    def __init__(self, table_id, capacity):
        self.table_id = table_id
        self.capacity = capacity
        self.busy_until = 0.0
        self.used_time = 0.0

    def is_free(self, current_time):
        return self.busy_until <= current_time


class CombinedTable:
    def __init__(self, left_table, right_table):
        self.left_table = left_table
        self.right_table = right_table
        self.table_id = f"{left_table.table_id}+{right_table.table_id}"
        self.capacity = left_table.capacity + right_table.capacity

    def is_free(self, current_time):
        return self.left_table.is_free(current_time) and self.right_table.is_free(current_time)

    def occupy(self, current_time, dining_time):
        end_time = current_time + dining_time
        self.left_table.used_time += dining_time
        self.right_table.used_time += dining_time
        self.left_table.busy_until = end_time
        self.right_table.busy_until = end_time


class SimulationResult:
    def __init__(self, mode_name):
        self.mode_name = mode_name
        self.total_groups = 0
        self.served_groups = 0
        self.unserved_groups = 0
        self.total_customers = 0
        self.served_customers = 0
        self.unserved_customers = 0
        self.avg_wait_time = 0.0
        self.max_wait_time = 0.0
        self.avg_table_utilization = 0.0
        self.total_revenue = 0.0
        self.timeline_wait = []
        self.timeline_queue = []
        self.group_records = []
        self.size_distribution = Counter()


class RestaurantSimulator:
    def __init__(self, table_config, simulation_minutes):
        self.table_config = table_config
        self.simulation_minutes = simulation_minutes
        self.max_wait_time = float("inf")
        self.revenue_per_customer = 0.0

    def _build_tables(self):
        tables = []
        table_id = 1
        for cap, count in self.table_config:
            for _ in range(count):
                tables.append(TableUnit(table_id, cap))
                table_id += 1
        return tables

    def _generate_groups(
        self,
        total_groups,
        mean_group_size,
        std_group_size,
        mean_dining_time,
        std_dining_time,
        seed
    ):
        raise ValueError("This version requires CSV input. Please select a CSV file with columns: arrival_time, group_size, dining_time")

    def _load_groups_from_csv(self, path):
        groups = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"arrival_time", "group_size", "dining_time"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("CSV 必须包含列: arrival_time, group_size, dining_time")

            for i, row in enumerate(reader, start=1):
                groups.append(
                    Group(
                        i,
                        float(row["arrival_time"]),
                        int(row["group_size"]),
                        float(row["dining_time"]),
                    )
                )
        return groups

    def get_groups(
        self,
        use_csv,
        csv_path,
        total_groups,
        mean_group_size,
        std_group_size,
        mean_dining_time,
        std_dining_time,
        seed
    ):
        if use_csv and csv_path:
            return self._load_groups_from_csv(csv_path)
        return self._generate_groups(
            total_groups,
            mean_group_size,
            std_group_size,
            mean_dining_time,
            std_dining_time,
            seed,
        )


    def _finalize_remaining_waiting(self, waiting, result, current_time):
        """Mark all remaining waiting groups as unserved when simulation ends or progress is impossible."""
        while waiting:
            group = waiting.popleft()
            waited = max(0.0, current_time - group.arrival_time)
            result.unserved_groups += 1
            result.unserved_customers += group.group_size
            result.group_records.append({
                "group_id": group.gid,
                "arrival_time": round(group.arrival_time, 2),
                "group_size": group.group_size,
                "dining_time": group.dining_time,
                "wait_time": round(waited, 2),
                "served": 0,
                "assigned_table": "None",
            })

    def run_mode_1(self, groups):
        result = SimulationResult("Mode 1: Fixed Tables")
        result.total_groups = len(groups)
        result.total_customers = sum(g.group_size for g in groups)
        result.size_distribution = Counter(g.group_size for g in groups)

        tables = self._build_tables()
        waiting = deque()
        idx = 0
        current_time = 0
        total_wait = 0.0
        max_wait = 0.0

        while current_time <= self.simulation_minutes or idx < len(groups):
            while idx < len(groups) and groups[idx].arrival_time <= current_time:
                waiting.append(groups[idx])
                idx += 1

            new_queue = deque()
            served_this_round = []

            while waiting:
                group = waiting.popleft()
                waited = current_time - group.arrival_time

                if waited > self.max_wait_time:
                    result.unserved_groups += 1
                    result.unserved_customers += group.group_size
                    result.group_records.append({
                        "group_id": group.gid,
                        "arrival_time": round(group.arrival_time, 2),
                        "group_size": group.group_size,
                        "dining_time": group.dining_time,
                        "wait_time": round(waited, 2),
                        "served": 0,
                        "assigned_table": "None",
                    })
                    continue

                free_candidates = [
                    t for t in tables
                    if t.is_free(current_time) and t.capacity >= group.group_size
                ]

                if free_candidates:
                    best_table = min(
                        free_candidates,
                        key=lambda t: (t.capacity - group.group_size, t.capacity, t.table_id)
                    )
                    best_table.used_time += group.dining_time
                    best_table.busy_until = current_time + group.dining_time

                    result.served_groups += 1
                    result.served_customers += group.group_size
                    total_wait += waited
                    max_wait = max(max_wait, waited)
                    result.total_revenue += group.group_size * self.revenue_per_customer
                    served_this_round.append(waited)

                    result.group_records.append({
                        "group_id": group.gid,
                        "arrival_time": round(group.arrival_time, 2),
                        "group_size": group.group_size,
                        "dining_time": group.dining_time,
                        "wait_time": round(waited, 2),
                        "served": 1,
                        "assigned_table": f"T{best_table.table_id}(cap={best_table.capacity})",
                    })
                else:
                    new_queue.append(group)

            waiting = new_queue
            avg_wait_now = sum(served_this_round) / len(served_this_round) if served_this_round else 0
            result.timeline_wait.append((current_time, avg_wait_now))
            result.timeline_queue.append((current_time, len(waiting)))
            current_time += 1

            if current_time > self.simulation_minutes and idx >= len(groups) and not waiting:
                break

        if waiting:
            self._finalize_remaining_waiting(waiting, result, current_time)

        result.avg_wait_time = total_wait / result.served_groups if result.served_groups else 0
        result.max_wait_time = max_wait
        total_capacity_time = len(tables) * self.simulation_minutes
        total_used_time = sum(min(t.used_time, self.simulation_minutes) for t in tables)
        result.avg_table_utilization = total_used_time / total_capacity_time if total_capacity_time else 0
        return result

    def run_mode_2(self, groups):
        result = SimulationResult("Mode 2: Flexible Combined Tables")
        result.total_groups = len(groups)
        result.total_customers = sum(g.group_size for g in groups)
        result.size_distribution = Counter(g.group_size for g in groups)

        tables = self._build_tables()
        waiting = deque()
        idx = 0
        current_time = 0
        total_wait = 0.0
        max_wait = 0.0

        while current_time <= self.simulation_minutes or idx < len(groups):
            while idx < len(groups) and groups[idx].arrival_time <= current_time:
                waiting.append(groups[idx])
                idx += 1

            new_queue = deque()
            served_this_round = []

            while waiting:
                group = waiting.popleft()
                waited = current_time - group.arrival_time

                if waited > self.max_wait_time:
                    result.unserved_groups += 1
                    result.unserved_customers += group.group_size
                    result.group_records.append({
                        "group_id": group.gid,
                        "arrival_time": round(group.arrival_time, 2),
                        "group_size": group.group_size,
                        "dining_time": group.dining_time,
                        "wait_time": round(waited, 2),
                        "served": 0,
                        "assigned_table": "None",
                    })
                    continue

                free_single = [
                    t for t in tables
                    if t.is_free(current_time) and t.capacity >= group.group_size
                ]
                single_choice = min(
                    free_single,
                    key=lambda t: (t.capacity - group.group_size, t.capacity, t.table_id)
                ) if free_single else None

                free_tables = [t for t in tables if t.is_free(current_time)]
                pair_candidates = []

                for i in range(len(free_tables)):
                    for j in range(i + 1, len(free_tables)):
                        ct = CombinedTable(free_tables[i], free_tables[j])
                        if ct.capacity >= group.group_size:
                            waste = ct.capacity - group.group_size
                            balance = abs(free_tables[i].capacity - free_tables[j].capacity)
                            pair_candidates.append((waste, balance, ct))

                pair_choice = min(
                    pair_candidates,
                    key=lambda x: (x[0], x[1], x[2].capacity)
                )[2] if pair_candidates else None

                use_pair = False
                if single_choice and pair_choice:
                    single_waste = single_choice.capacity - group.group_size
                    pair_waste = pair_choice.capacity - group.group_size
                    if pair_waste + 1 < single_waste:
                        use_pair = True
                elif pair_choice and not single_choice:
                    use_pair = True

                if use_pair:
                    pair_choice.occupy(current_time, group.dining_time)
                    assigned = pair_choice.table_id
                elif single_choice:
                    single_choice.used_time += group.dining_time
                    single_choice.busy_until = current_time + group.dining_time
                    assigned = f"T{single_choice.table_id}(cap={single_choice.capacity})"
                else:
                    new_queue.append(group)
                    continue

                result.served_groups += 1
                result.served_customers += group.group_size
                total_wait += waited
                max_wait = max(max_wait, waited)
                result.total_revenue += group.group_size * self.revenue_per_customer
                served_this_round.append(waited)

                result.group_records.append({
                    "group_id": group.gid,
                    "arrival_time": round(group.arrival_time, 2),
                    "group_size": group.group_size,
                    "dining_time": group.dining_time,
                    "wait_time": round(waited, 2),
                    "served": 1,
                    "assigned_table": assigned,
                })

            waiting = new_queue
            avg_wait_now = sum(served_this_round) / len(served_this_round) if served_this_round else 0
            result.timeline_wait.append((current_time, avg_wait_now))
            result.timeline_queue.append((current_time, len(waiting)))
            current_time += 1

            if current_time > self.simulation_minutes and idx >= len(groups) and not waiting:
                break

        if waiting:
            self._finalize_remaining_waiting(waiting, result, current_time)

        result.avg_wait_time = total_wait / result.served_groups if result.served_groups else 0
        result.max_wait_time = max_wait
        total_capacity_time = len(tables) * self.simulation_minutes
        total_used_time = sum(min(t.used_time, self.simulation_minutes) for t in tables)
        result.avg_table_utilization = total_used_time / total_capacity_time if total_capacity_time else 0
        return result


class RestaurantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant Simulation Comparison Tool")
        self.root.geometry("1380x860")

        self.csv_path = tk.StringVar()
        self.use_csv = tk.BooleanVar(value=True)
        self.zoom_percent = tk.IntVar(value=100)
        self.result_mode_1 = None
        self.result_mode_2 = None

        self._init_zoom_fonts()
        self._build_scrollable_container()
        self._build_ui()
        self.apply_zoom(100)

    def _init_zoom_fonts(self):
        """Store base font sizes so the interface can be zoomed safely."""
        self.base_font_sizes = {}
        for font_name in ["TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont"]:
            try:
                named_font = tkfont.nametofont(font_name)
                size = named_font.cget("size")
                self.base_font_sizes[font_name] = abs(int(size)) if size else 10
            except tk.TclError:
                self.base_font_sizes[font_name] = 10

    def _scaled_size(self, base_size):
        zoom = max(50, min(500, int(self.zoom_percent.get())))
        return max(6, int(round(base_size * zoom / 100)))

    def _canvas_font(self, base_size, weight="normal"):
        return ("Arial", self._scaled_size(base_size), weight)

    def apply_zoom(self, value=None):
        """Apply zoom to labels, entries, buttons, text boxes, and chart text."""
        if value is not None:
            self.zoom_percent.set(int(float(value)))

        zoom = max(50, min(500, int(self.zoom_percent.get())))
        if hasattr(self, "zoom_label_var"):
            self.zoom_label_var.set(f"{zoom}%")

        for font_name, base_size in self.base_font_sizes.items():
            try:
                tkfont.nametofont(font_name).configure(size=self._scaled_size(base_size))
            except tk.TclError:
                pass

        default_size = self._scaled_size(10)
        if hasattr(self, "style"):
            self.style.configure("TLabel", font=("Arial", default_size))
            self.style.configure("TButton", font=("Arial", default_size))
            self.style.configure("TCheckbutton", font=("Arial", default_size))
            self.style.configure("TEntry", font=("Arial", default_size))
            self.style.configure("TLabelframe.Label", font=("Arial", default_size, "bold"))
            self.style.configure("Title.TLabel", font=("Arial", default_size, "bold"))

        text_font = ("Consolas", self._scaled_size(10))
        if hasattr(self, "mode1_text"):
            self.mode1_text.configure(font=text_font)
        if hasattr(self, "mode2_text"):
            self.mode2_text.configure(font=text_font)

        if self.result_mode_1 is not None and self.result_mode_2 is not None:
            self.draw_visualization(self.result_mode_1, self.result_mode_2)

        if hasattr(self, "main_canvas") and hasattr(self, "main_container"):
            self.root.update_idletasks()
            required_width = self.main_container.winfo_reqwidth()
            visible_width = self.main_canvas.winfo_width()
            self.main_canvas.itemconfig(self.canvas_window, width=max(required_width, visible_width))
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _build_scrollable_container(self):
        self.outer_frame = ttk.Frame(self.root)
        self.outer_frame.pack(fill="both", expand=True)

        # Grid layout allows both vertical and horizontal scrollbars.
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        self.main_canvas = tk.Canvas(self.outer_frame, highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = ttk.Scrollbar(self.outer_frame, orient="vertical", command=self.main_canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        self.h_scroll = ttk.Scrollbar(self.outer_frame, orient="horizontal", command=self.main_canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.main_canvas.configure(
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
        )

        self.main_container = ttk.Frame(self.main_canvas)
        self.canvas_window = self.main_canvas.create_window(
            (0, 0), window=self.main_container, anchor="nw"
        )

        def update_scroll_region():
            self.main_container.update_idletasks()
            required_width = self.main_container.winfo_reqwidth()
            visible_width = self.main_canvas.winfo_width()
            self.main_canvas.itemconfig(self.canvas_window, width=max(required_width, visible_width))
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        def on_frame_configure(event):
            update_scroll_region()

        def on_canvas_configure(event):
            update_scroll_region()

        self.main_container.bind("<Configure>", on_frame_configure)
        self.main_canvas.bind("<Configure>", on_canvas_configure)

        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_shift_mousewheel(event):
            self.main_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        # Drag on the blank canvas area to pan the page.
        def _start_drag(event):
            self.main_canvas.scan_mark(event.x, event.y)

        def _drag_canvas(event):
            self.main_canvas.scan_dragto(event.x, event.y, gain=1)

        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.main_canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)
        self.main_canvas.bind("<ButtonPress-1>", _start_drag)
        self.main_canvas.bind("<B1-Motion>", _drag_canvas)
    def _build_ui(self):
        self.style = ttk.Style(self.root)

        top_frame = ttk.Frame(self.main_container, padding=10)
        top_frame.pack(fill="x")

        zoom_frame = ttk.LabelFrame(top_frame, text="Display Zoom", padding=10)
        zoom_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(zoom_frame, text="Zoom").pack(side="left", padx=(0, 8))
        ttk.Scale(
            zoom_frame,
            from_=50,
            to=500,
            orient="horizontal",
            variable=self.zoom_percent,
            command=self.apply_zoom,
            length=420,
        ).pack(side="left", padx=5)
        self.zoom_label_var = tk.StringVar(value="100%")
        ttk.Label(zoom_frame, textvariable=self.zoom_label_var, width=6).pack(side="left", padx=8)
        ttk.Label(zoom_frame, text="Range: 50% - 500%").pack(side="left", padx=8)

        input_frame = ttk.LabelFrame(top_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="Restaurant Inputs", style="Title.TLabel").grid(
            row=0, column=0, columnspan=8, sticky="w", pady=(0, 6)
        )

        restaurant_params = [
            ("Simulation Minutes", "180"),
            ("2-seat Tables", "4"),
            ("4-seat Tables", "6"),
            ("6-seat Tables", "2"),
        ]

        self.entries = {}

        for idx, (label, default) in enumerate(restaurant_params):
            row = 1 + idx // 4
            col = (idx % 4) * 2
            ttk.Label(input_frame, text=label).grid(row=row, column=col, padx=6, pady=4, sticky="w")
            entry = ttk.Entry(input_frame, width=12)
            entry.insert(0, default)
            entry.grid(row=row, column=col + 1, padx=6, pady=4)
            self.entries[label] = entry

        csv_frame = ttk.Frame(input_frame)
        csv_frame.grid(row=3, column=0, columnspan=8, sticky="w", pady=10)
        ttk.Checkbutton(csv_frame, text="Use CSV Input", variable=self.use_csv).pack(side="left", padx=5)
        ttk.Entry(csv_frame, textvariable=self.csv_path, width=70).pack(side="left", padx=5)
        ttk.Button(csv_frame, text="Browse CSV", command=self.browse_csv).pack(side="left", padx=5)
        ttk.Label(csv_frame, text="CSV columns: arrival_time, group_size, dining_time").pack(side="left", padx=10)

        button_frame = ttk.Frame(top_frame, padding=(0, 10))
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="Run Both Modes", command=self.run_simulation).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Export Mode 1 CSV", command=lambda: self.export_result(1)).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Export Mode 2 CSV", command=lambda: self.export_result(2)).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output).pack(side="left", padx=6)

        middle_frame = ttk.Frame(self.main_container, padding=10)
        middle_frame.pack(fill="both", expand=True)

        left_panel = ttk.LabelFrame(middle_frame, text="Mode 1 Result", padding=10)
        left_panel.pack(side="left", fill="both", expand=True, padx=5)

        self.mode1_text = tk.Text(left_panel, width=50, height=14)
        self.mode1_text.pack(fill="both", expand=True)

        right_panel = ttk.LabelFrame(middle_frame, text="Mode 2 Result", padding=10)
        right_panel.pack(side="left", fill="both", expand=True, padx=5)

        self.mode2_text = tk.Text(right_panel, width=50, height=14)
        self.mode2_text.pack(fill="both", expand=True)

        bottom_frame = ttk.LabelFrame(self.main_container, text="Visualization", padding=10)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(bottom_frame, bg="white", height=380)
        self.canvas.pack(fill="both", expand=True)

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_path.set(path)
            self.use_csv.set(True)

    def get_inputs(self):
        try:
            input_data = {
                "simulation_minutes": int(self.entries["Simulation Minutes"].get()),
                "table_config": [
                    (2, int(self.entries["2-seat Tables"].get())),
                    (4, int(self.entries["4-seat Tables"].get())),
                    (6, int(self.entries["6-seat Tables"].get())),
                ],
                "use_csv": self.use_csv.get(),
                "csv_path": self.csv_path.get().strip(),
            }

            if input_data["simulation_minutes"] <= 0:
                raise ValueError("Simulation Minutes must be > 0.")
            if sum(count for _, count in input_data["table_config"]) <= 0:
                raise ValueError("At least one table is required.")
            if not input_data["use_csv"] or not input_data["csv_path"]:
                raise ValueError("Please enable CSV input and select a valid CSV file.")

            return input_data
        except ValueError as e:
            raise ValueError(str(e) if str(e) else "Please make sure all input values are valid numbers.")

    def run_simulation(self):
        try:
            input_data = self.get_inputs()
            simulator = RestaurantSimulator(
                table_config=input_data["table_config"],
                simulation_minutes=input_data["simulation_minutes"],
            )

            groups = simulator.get_groups(
                use_csv=input_data["use_csv"],
                csv_path=input_data["csv_path"],
                total_groups=0,
                mean_group_size=0,
                std_group_size=0,
                mean_dining_time=0,
                std_dining_time=0,
                seed=0,
            )

            self.result_mode_1 = simulator.run_mode_1(groups)
            self.result_mode_2 = simulator.run_mode_2(groups)

            self.show_result(self.mode1_text, self.result_mode_1)
            self.show_result(self.mode2_text, self.result_mode_2)
            self.draw_visualization(self.result_mode_1, self.result_mode_2)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_result(self, widget, result):
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, f"{result.mode_name}\n")
        widget.insert(tk.END, "=" * 42 + "\n")
        widget.insert(tk.END, f"Total Groups: {result.total_groups}\n")
        widget.insert(tk.END, f"Served Groups: {result.served_groups}\n")
        widget.insert(tk.END, f"Unserved Groups: {result.unserved_groups}\n")
        widget.insert(tk.END, f"Total Customers: {result.total_customers}\n")
        widget.insert(tk.END, f"Served Customers: {result.served_customers}\n")
        widget.insert(tk.END, f"Unserved Customers: {result.unserved_customers}\n")
        widget.insert(tk.END, f"Remaining Groups in Queue: {result.unserved_groups}\n")
        widget.insert(tk.END, f"Remaining Customers in Queue: {result.unserved_customers}\n")
        widget.insert(tk.END, f"Average Wait Time: {result.avg_wait_time:.2f} min\n")
        widget.insert(tk.END, f"Maximum Wait Time: {result.max_wait_time:.2f} min\n")
        widget.insert(tk.END, f"Table Utilization: {result.avg_table_utilization:.2%}\n")
        widget.insert(tk.END, "\n")
        widget.insert(tk.END, "Group Size Distribution:\n")
        for size in sorted(result.size_distribution):
            widget.insert(tk.END, f"  Size {size}: {result.size_distribution[size]} groups\n")

        avg_by_size = self._avg_wait_by_group_size(result)
        widget.insert(tk.END, "\nAverage Wait by Group Size (served groups):\n")
        for size in sorted(result.size_distribution):
            if size in avg_by_size:
                widget.insert(tk.END, f"  Size {size}: {avg_by_size[size]:.2f} min\n")
            else:
                widget.insert(tk.END, f"  Size {size}: N/A\n")

    def _avg_wait_by_group_size(self, result):
        """Return average wait time for served groups, grouped by group size."""
        grouped_waits = {}
        for record in result.group_records:
            if int(record.get("served", 0)) != 1:
                continue
            size = int(record["group_size"])
            grouped_waits.setdefault(size, []).append(float(record["wait_time"]))
        return {size: sum(values) / len(values) for size, values in grouped_waits.items()}

    def _draw_text_table(self, x, y, title, headers, rows, col_widths, row_height=24):
        """Draw a simple text table on the visualization canvas."""
        self.canvas.create_text(x, y, text=title, anchor="w", font=self._canvas_font(12, "bold"))
        y += 28
        current_x = x
        for header, width in zip(headers, col_widths):
            self.canvas.create_rectangle(current_x, y, current_x + width, y + row_height, outline="black")
            self.canvas.create_text(current_x + 6, y + row_height / 2, text=header, anchor="w", font=self._canvas_font(9, "bold"))
            current_x += width
        y += row_height
        for row in rows:
            current_x = x
            for value, width in zip(row, col_widths):
                self.canvas.create_rectangle(current_x, y, current_x + width, y + row_height, outline="black")
                self.canvas.create_text(current_x + 6, y + row_height / 2, text=str(value), anchor="w", font=self._canvas_font(9))
                current_x += width
            y += row_height
        return y

    def draw_visualization(self, r1, r2):
        self.canvas.delete("all")
        self.canvas.update_idletasks()

        canvas_width = max(1100, self.canvas.winfo_width())
        canvas_height = max(720, self.canvas.winfo_height())

        self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height), height=min(620, canvas_height))

        self.canvas.create_text(
            canvas_width / 2, 20,
            text="Mode 1 vs Mode 2 Comparison",
            font=self._canvas_font(15, "bold")
        )

        left_x = 50
        top_y = 60
        chart_width = canvas_width * 0.42
        chart_height = 230
        bottom_y = top_y + chart_height

        metrics = [
            ("Served Groups", r1.served_groups, r2.served_groups),
            ("Avg Wait", r1.avg_wait_time, r2.avg_wait_time),
            ("Utilization %", r1.avg_table_utilization * 100, r2.avg_table_utilization * 100),
            ("Remaining Customers", r1.unserved_customers, r2.unserved_customers),
        ]

        max_value = max(max(a, b) for _, a, b in metrics) or 1

        self.canvas.create_line(left_x, top_y, left_x, bottom_y, width=2)
        self.canvas.create_line(left_x, bottom_y, left_x + chart_width, bottom_y, width=2)

        group_gap = chart_width / len(metrics)
        bar_width = min(30, group_gap / 4)

        for i, (label, v1, v2) in enumerate(metrics):
            x_base = left_x + i * group_gap + group_gap * 0.22
            h1 = (v1 / max_value) * (chart_height - 35)
            h2 = (v2 / max_value) * (chart_height - 35)

            self.canvas.create_rectangle(
                x_base, bottom_y - h1,
                x_base + bar_width, bottom_y,
                fill="#4F81BD", outline="black"
            )
            self.canvas.create_rectangle(
                x_base + bar_width + 8, bottom_y - h2,
                x_base + 2 * bar_width + 8, bottom_y,
                fill="#C0504D", outline="black"
            )

            self.canvas.create_text(
                x_base + bar_width / 2,
                bottom_y - h1 - 10,
                text=f"{v1:.1f}",
                font=self._canvas_font(8)
            )
            self.canvas.create_text(
                x_base + bar_width + 8 + bar_width / 2,
                bottom_y - h2 - 10,
                text=f"{v2:.1f}",
                font=self._canvas_font(8)
            )

            self.canvas.create_text(
                x_base + bar_width,
                bottom_y + 18,
                text=label,
                font=self._canvas_font(9)
            )

        legend_y = bottom_y + 40
        self.canvas.create_rectangle(left_x + 20, legend_y, left_x + 40, legend_y + 15, fill="#4F81BD", outline="black")
        self.canvas.create_text(left_x + 90, legend_y + 8, text="Mode 1", font=self._canvas_font(10))
        self.canvas.create_rectangle(left_x + 170, legend_y, left_x + 190, legend_y + 15, fill="#C0504D", outline="black")
        self.canvas.create_text(left_x + 240, legend_y + 8, text="Mode 2", font=self._canvas_font(10))

        line_left = canvas_width * 0.55
        line_top = 60
        line_width = canvas_width * 0.36
        line_height = 230
        line_bottom = line_top + line_height

        self.canvas.create_text(
            line_left + line_width / 2, 40,
            text="Queue Length Over Time",
            font=self._canvas_font(12, "bold")
        )

        self.canvas.create_line(line_left, line_top, line_left, line_bottom, width=2)
        self.canvas.create_line(line_left, line_bottom, line_left + line_width, line_bottom, width=2)

        max_time = max([t for t, _ in r1.timeline_queue] + [t for t, _ in r2.timeline_queue] + [1])
        max_q = max([q for _, q in r1.timeline_queue] + [q for _, q in r2.timeline_queue] + [1])

        for i in range(6):
            y = line_top + i * line_height / 5
            q_val = max_q - i * max_q / 5
            self.canvas.create_line(line_left - 5, y, line_left, y)
            self.canvas.create_text(line_left - 22, y, text=f"{q_val:.0f}", font=self._canvas_font(8))

        for i in range(6):
            x = line_left + i * line_width / 5
            t_val = i * max_time / 5
            self.canvas.create_line(x, line_bottom, x, line_bottom + 5)
            self.canvas.create_text(x, line_bottom + 15, text=f"{t_val:.0f}", font=self._canvas_font(8))

        def draw_series(series, color):
            if len(series) < 2:
                return
            pts = []
            for t, q in series:
                x = line_left + (t / max_time) * line_width
                y = line_bottom - (q / max_q) * (line_height - 10)
                pts.extend([x, y])
            self.canvas.create_line(*pts, fill=color, width=2)

        draw_series(r1.timeline_queue, "#4F81BD")
        draw_series(r2.timeline_queue, "#C0504D")

        info_y = bottom_y + 95
        remaining_rows = [
            ["Mode 1", r1.unserved_groups, r1.unserved_customers],
            ["Mode 2", r2.unserved_groups, r2.unserved_customers],
        ]
        self._draw_text_table(
            left_x,
            info_y,
            "Customers Still Waiting at the End",
            ["Mode", "Groups", "Customers"],
            remaining_rows,
            [110, 110, 130],
            row_height=max(24, self._scaled_size(16))
        )

        avg_by_size_1 = self._avg_wait_by_group_size(r1)
        avg_by_size_2 = self._avg_wait_by_group_size(r2)
        all_sizes = sorted(set(avg_by_size_1) | set(avg_by_size_2) | set(r1.size_distribution) | set(r2.size_distribution))
        group_size_rows = []
        for size in all_sizes:
            v1 = avg_by_size_1.get(size)
            v2 = avg_by_size_2.get(size)
            group_size_rows.append([
                size,
                "N/A" if v1 is None else f"{v1:.2f} min",
                "N/A" if v2 is None else f"{v2:.2f} min",
            ])

        self._draw_text_table(
            line_left,
            info_y,
            "Average Wait Time by Group Size",
            ["Group Size", "Mode 1", "Mode 2"],
            group_size_rows,
            [130, 150, 150],
            row_height=max(24, self._scaled_size(16))
        )


    def export_result(self, mode):
        result = self.result_mode_1 if mode == 1 else self.result_mode_2
        if result is None:
            messagebox.showwarning("Warning", "Please run the simulation first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "group_id",
                    "arrival_time",
                    "group_size",
                    "dining_time",
                    "wait_time",
                    "served",
                    "assigned_table",
                ]
            )
            writer.writeheader()
            writer.writerows(result.group_records)

        messagebox.showinfo("Done", "Result CSV exported successfully.")

    def clear_output(self):
        self.mode1_text.delete("1.0", tk.END)
        self.mode2_text.delete("1.0", tk.END)
        self.canvas.delete("all")
        self.result_mode_1 = None
        self.result_mode_2 = None


if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantApp(root)
    root.mainloop()