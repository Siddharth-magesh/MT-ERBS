import tkinter as tk
from tkinter import ttk
import random, math, time, csv, threading
from collections import deque, defaultdict
import numpy as np
import pandas as pd

# ---------------------------
# Configuration
# ---------------------------
GRID_W = 12         # width (columns)
GRID_H = 8          # height (rows)
CELL_PIX = 60       # pixels per cell
WINDOW_WIDTH = GRID_W * CELL_PIX + 350   # extra panel
WINDOW_HEIGHT = GRID_H * CELL_PIX

UPDATE_MS = 300     # GUI update interval (ms) base
SIM_SPEED = 1.0     # multiplier for simulation speed

# Probabilities for cell types (only 'signal' cells have signals)
P_SIGNAL = 0.20
P_BLOCK = 0.06
P_HEAVY = 0.12      # heavy traffic generator probability

# IoT / AI parameters (simulated)
SENSOR_REPORT_INTERVAL = 1.0   # seconds (simulated)
AI_DECISION_LATENCY = 0.25     # seconds to make a decision
PREDICTION_HORIZON = 30        # seconds for ETA prediction

# Logging file
LOG_CSV = "simulation_log.csv"

# ---------------------------
# Cell Types
# ---------------------------
CELL_SIGNAL = "signal"
CELL_ROAD = "road"
CELL_BLOCK = "block"
CELL_HEAVY = "heavy"   # generates higher arrivals

CELL_NAMES = {
    CELL_SIGNAL: "Signal",
    CELL_ROAD: "Road",
    CELL_BLOCK: "Blocked",
    CELL_HEAVY: "HeavyTraffic",
}

# ---------------------------
# Helper functions
# ---------------------------
def within_grid(x, y):
    return 0 <= x < GRID_W and 0 <= y < GRID_H

def neighbors(x, y):
    # 4-neighborhood (up/down/left/right)
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x+dx, y+dy
        if within_grid(nx, ny):
            yield (nx, ny)

def manhattan(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

# ---------------------------
# Simulation objects
# ---------------------------
class Signal:
    def __init__(self, pos):
        self.pos = pos
        self.state = "RED"   # "GREEN" or "RED"
        self.timer = 0
        self.green_duration = 6
        self.red_duration = 6
        self.override = False   # server-issued override (True until cleared)
        self.sensor = Sensor(self)
        # queue length is tracked externally in GridState; sensor reads it

    def step_timer(self, dt=1.0):
        if self.override:
            # when overridden, state is controlled by server externally
            return
        self.timer += dt
        if self.state == "GREEN" and self.timer >= self.green_duration:
            self.state = "RED"; self.timer = 0
        elif self.state == "RED" and self.timer >= self.red_duration:
            self.state = "GREEN"; self.timer = 0

    def set_green(self):
        self.state = "GREEN"; self.timer = 0; self.override = True

    def set_red(self):
        self.state = "RED"; self.timer = 0; self.override = True

    def clear_override(self):
        self.override = False
        self.timer = 0

class Sensor:
    def __init__(self, signal):
        self.signal = signal
        self.last_report = None   # dict

    def sample(self, grid_state):
        # Build a simple observation for the intersection
        x,y = self.signal.pos
        q = grid_state.queues[(x,y)]
        local_speed = grid_state.estimated_speed_at((x,y))
        incident = grid_state.incidents.get((x,y), None)
        obs = {
            "pos": (x,y),
            "queue": q,
            "speed": local_speed,
            "incident": incident,
            "timestamp": time.time()
        }
        self.last_report = obs
        return obs

class GridState:
    def __init__(self, layout):
        # layout: dict (x,y)->cell_type
        self.layout = layout
        # queue counts at intersections/cells
        self.queues = defaultdict(int)
        # incidents/blocks: dict pos -> description
        self.incidents = {}
        # vehicle generators for heavy cells
        self.generators = []
        # initialize queues with small baseline
        for pos, t in self.layout.items():
            if t == CELL_BLOCK:
                self.queues[pos] = 0
            elif t == CELL_HEAVY:
                self.queues[pos] = random.randint(6,12)
                self.generators.append(pos)
            else:
                self.queues[pos] = random.randint(0,4)

    def step_traffic_arrivals(self):
        # Poisson-like arrivals per cell, heavier at heavy generators
        for pos, t in self.layout.items():
            if t == CELL_BLOCK:
                continue
            if t == CELL_HEAVY:
                self.queues[pos] += np.random.poisson(1.6)
            else:
                self.queues[pos] += np.random.poisson(0.6)
            # cap queue to reasonable max
            self.queues[pos] = min(self.queues[pos], 80)

    def estimated_speed_at(self, pos):
        # Simple model: speed inversely proportional to local queue
        q = self.queues.get(pos, 0)
        base = 12.0   # m/s nominal
        speed = base * (1.0 / (1.0 + 0.08 * q))
        return speed

    def drain_queue(self, pos, count):
        # simulate vehicles passing through intersection
        available = self.queues.get(pos, 0)
        actual = min(available, count)
        self.queues[pos] = max(0, available - actual)
        return actual

# ---------------------------
# Server + AI (simulated)
# ---------------------------
class Server:
    def __init__(self, grid_state, signals):
        self.grid = grid_state
        self.signals = signals   # dict pos->Signal
        self.log = []
        self.lock = threading.Lock()
        self.last_decision_time = 0

    def receive_sensor_reports(self):
        # Poll sensors (synchronously here)
        reports = []
        for s in self.signals.values():
            obs = s.sensor.sample(self.grid)
            reports.append(obs)
        return reports

    def compute_route(self, start, goal):
        # Simple breadth-first shortest path ignoring blocks
        queue = deque([start])
        prev = {start: None}
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for nb in neighbors(*cur):
                if nb in prev: continue
                if self.grid.layout.get(nb) == CELL_BLOCK:
                    continue
                prev[nb] = cur
                queue.append(nb)
        # backtrack
        if goal not in prev:
            return [start]
        path = []
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    def predict_eta(self, path, current_pos):
        # Simple ETA: sum of (distance / predicted speed) with small decision latency
        eta = 0.0
        for idx in range(len(path)-1):
            pos = path[idx]
            speed = self.grid.estimated_speed_at(pos)
            # distance normalized to 1 unit per cell
            step_time = 1.0 / max(0.5, speed/12.0) * 3.0  # scaled factor
            eta += step_time
        # add decision latency and small noise
        eta += AI_DECISION_LATENCY + random.uniform(0,0.5)
        return eta

    def issue_preemption(self, ambulance_pos, corridor, severity=1):
        # Main decision: set the signal at ambulance's next node to GREEN
        # and set neighboring signals to RED to prevent cross-flow; throttle upstream feeders
        with self.lock:
            tstamp = time.time()
            decision = {
                "time": tstamp,
                "ambulance_pos": ambulance_pos,
                "corridor": corridor.copy(),
                "actions": []
            }
            # For each node on corridor, we may set green; prioritize immediate next hop
            if len(corridor) >= 2:
                next_node = corridor[1]
            else:
                next_node = corridor[0]
            # set next_node green
            if next_node in self.signals:
                self.signals[next_node].set_green()
                decision["actions"].append(("set_green", next_node))
            # set nearby non-corridor signals red (neighbors within manhattan <=2)
            for pos, sig in self.signals.items():
                if pos == next_node: continue
                if manhattan(pos, next_node) <= 2:
                    sig.set_red()
                    decision["actions"].append(("set_red", pos))
            # upstream gating: for neighbors that feed into corridor[0], temporarily reduce outflow by leaving signals red
            # (simulated by leaving overrides on)
            decision["note"] = "preemption: set next green & neighbors red; upstream gating applied"
            self.log.append(decision)
            self.last_decision_time = tstamp
            print("[SERVER] Decision at", time.strftime("%H:%M:%S", time.localtime(tstamp)), decision["note"])
            return decision

    def clear_overrides_after(self, seconds=6):
        # clear overrides after some time to allow signals to resume normal operation
        with self.lock:
            tnow = time.time()
            for pos, sig in self.signals.items():
                if sig.override and (tnow - self.last_decision_time) > seconds:
                    sig.clear_override()
                    print("[SERVER] Cleared override for", pos)

# ---------------------------
# Ambulance Agent
# ---------------------------
class AmbulanceAgent:
    def __init__(self, start, goal, grid_state, server):
        self.pos = start
        self.start = start
        self.goal = goal
        self.grid = grid_state
        self.server = server
        self.path = server.compute_route(start, goal)
        self.curr_index = 0
        self.travel_time = 0.0
        self.blocking_time = 0.0
        self.speed = 1.0  # cells per step baseline
        self.severity = 1
        self.completed = False
        self.logs = []

    def step(self, dt=1.0):
        if self.completed:
            return
        # If at goal
        if self.pos == self.goal:
            self.completed = True
            return

        # Recompute path occasionally to react to incidents
        if random.random() < 0.02:
            self.path = self.server.compute_route(self.pos, self.goal)

        # Ask server to preempt signals if necessary
        # Decide if ambulance should request preemption when within 3 cells of next intersections
        if self.curr_index < len(self.path)-1:
            lookahead = self.path[self.curr_index:self.curr_index+3]
            eta = self.server.predict_eta(lookahead, self.pos)
            # if ETA within horizon, request preemption
            if eta < PREDICTION_HORIZON:
                decision = self.server.issue_preemption(self.pos, self.path, severity=self.severity)
                self.logs.append(("preempt_request", time.time(), decision))

        # Movement decision: if next cell is blocked or has extreme queue, maybe wait or be blocked
        next_index = self.curr_index + 1
        if next_index >= len(self.path):
            # already at end
            self.completed = True
            return
        next_pos = self.path[next_index]
        # If blocked cell, wait
        if self.grid.layout.get(next_pos) == CELL_BLOCK:
            self.blocking_time += dt
            self.travel_time += dt
            return
        # If there's a signal at next_pos and it's RED, we may have to wait unless the server has set green
        if next_pos in self.server.signals:
            sig = self.server.signals[next_pos]
            if sig.state == "RED":
                # check if override is active (server-controlled) and it's red -> must wait
                self.blocking_time += dt
                self.travel_time += dt
                return
        # Otherwise, attempt to move: movement speed influenced by local queue at current pos
        local_speed = self.grid.estimated_speed_at(self.pos)
        # normalize speed to #cells per step (we use dt=1 -> either 0 or 1 step)
        move_prob = min(1.0, local_speed / 12.0)
        if random.random() < move_prob:
            # drain some vehicles at current pos to simulate clearing path
            drained = self.grid.drain_queue(self.pos, count=3)
            self.pos = next_pos
            self.curr_index = next_index
            self.travel_time += dt
            self.logs.append(("moved", time.time(), self.pos))
        else:
            self.blocking_time += dt
            self.travel_time += dt

# ---------------------------
# GUI and Visualization
# ---------------------------
class MT_GUI:
    def __init__(self, root):
        self.root = root
        root.title("MT_ERBS Expanded Simulation")
        self.canvas = tk.Canvas(root, width=GRID_W*CELL_PIX, height=GRID_H*CELL_PIX, bg="white")
        self.canvas.grid(row=0, column=0, rowspan=20)
        # right panel for controls and status
        self.panel = tk.Frame(root, width=350)
        self.panel.grid(row=0, column=1, sticky="n")

        # build layout map
        self.layout = {}
        self.signals = {}
        for y in range(GRID_H):
            for x in range(GRID_W):
                r = random.random()
                if r < P_SIGNAL:
                    t = CELL_SIGNAL
                elif r < P_SIGNAL + P_BLOCK:
                    t = CELL_BLOCK
                elif r < P_SIGNAL + P_BLOCK + P_HEAVY:
                    t = CELL_HEAVY
                else:
                    t = CELL_ROAD
                # ensure start/end corners are not block
                if (x,y) in [(0,0), (GRID_W-1, GRID_H-1)]:
                    t = CELL_ROAD
                self.layout[(x,y)] = t

        # create grid state
        self.grid_state = GridState(self.layout)

        # build signals dictionary for only signal cells
        for pos, t in self.layout.items():
            if t == CELL_SIGNAL:
                sig = Signal(pos)
                self.signals[pos] = sig

        # server
        self.server = Server(self.grid_state, self.signals)

        # ambulance placeholders (select start/end by clicking)
        self.start = (0,0)
        self.goal = (GRID_W-1, GRID_H-1)
        self.ambulance = AmbulanceAgent(self.start, self.goal, self.grid_state, self.server)

        # GUI Controls
        self.status_text = tk.StringVar()
        self.status_text.set("Ready")
        ttk.Label(self.panel, text="MT_ERBS Simulation", font=("Arial",14,"bold")).pack(pady=6)
        ttk.Label(self.panel, textvariable=self.status_text, foreground="blue").pack()

        ttk.Label(self.panel, text="Click grid to set START (left) and END (right)").pack(pady=4)
        btn_frame = tk.Frame(self.panel)
        btn_frame.pack(pady=4)
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_sim)
        self.start_btn.grid(row=0, column=0, padx=4)
        self.pause_btn = ttk.Button(btn_frame, text="Pause", command=self.pause_sim, state="disabled")
        self.pause_btn.grid(row=0, column=1, padx=4)
        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_sim)
        self.reset_btn.grid(row=0, column=2, padx=4)

        ttk.Label(self.panel, text="Simulation speed:").pack(pady=6)
        self.speed_scale = ttk.Scale(self.panel, from_=0.2, to=3.0, value=1.0, orient=tk.HORIZONTAL, command=self.set_speed)
        self.speed_scale.pack(fill="x", padx=6)

        # info labels
        self.info = tk.Text(self.panel, height=18, width=40)
        self.info.pack(pady=6)
        self.info.insert("end", "Server / AI Log:\n")

        # bind clicks
        self.canvas.bind("<Button-1>", self.on_left_click)   # set start
        self.canvas.bind("<Button-3>", self.on_right_click)  # set end

        # simulation state
        self.running = False
        self._after_id = None
        self.log_rows = []

        # draw initial grid
        self.draw()

    def set_speed(self, val):
        global SIM_SPEED, UPDATE_MS
        SIM_SPEED = float(val)
        # note: update interval is multiplied by SIM_SPEED in loop

    def on_left_click(self, event):
        x = int(event.x // CELL_PIX)
        y = int(event.y // CELL_PIX)
        if within_grid(x,y) and self.layout[(x,y)] != CELL_BLOCK:
            self.start = (x,y)
            self.ambulance = AmbulanceAgent(self.start, self.goal, self.grid_state, self.server)
            self.info.insert("end", f"Start set to {self.start}\n")
            self.draw()

    def on_right_click(self, event):
        x = int(event.x // CELL_PIX)
        y = int(event.y // CELL_PIX)
        if within_grid(x,y) and self.layout[(x,y)] != CELL_BLOCK:
            self.goal = (x,y)
            self.ambulance = AmbulanceAgent(self.start, self.goal, self.grid_state, self.server)
            self.info.insert("end", f"Goal set to {self.goal}\n")
            self.draw()

    def start_sim(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.reset_btn.config(state="disabled")
        self.status_text.set("Running")
        # clear server log
        self.server.log = []
        # start background sensor-reporting thread if needed
        self._run_loop()

    def pause_sim(self):
        if not self.running:
            return
        self.running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.reset_btn.config(state="normal")
        self.status_text.set("Paused")
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def reset_sim(self):
        # reinitialize layout and state
        self.info.insert("end", "Resetting simulation...\n")
        # re-randomize layout but keep start/goal valid
        for pos in list(self.layout.keys()):
            r = random.random()
            if r < P_SIGNAL:
                t = CELL_SIGNAL
            elif r < P_SIGNAL + P_BLOCK:
                t = CELL_BLOCK
            elif r < P_SIGNAL + P_BLOCK + P_HEAVY:
                t = CELL_HEAVY
            else:
                t = CELL_ROAD
            if pos in [(0,0),(GRID_W-1, GRID_H-1)]:
                t = CELL_ROAD
            self.layout[pos] = t
        self.grid_state = GridState(self.layout)
        self.signals = {}
        for pos,t in self.layout.items():
            if t == CELL_SIGNAL:
                self.signals[pos] = Signal(pos)
        self.server = Server(self.grid_state, self.signals)
        self.ambulance = AmbulanceAgent(self.start, self.goal, self.grid_state, self.server)
        self.log_rows = []
        self.info.insert("end", "Reset done.\n")
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        # draw cells
        for y in range(GRID_H):
            for x in range(GRID_W):
                x0, y0 = x*CELL_PIX, y*CELL_PIX
                x1, y1 = x0+CELL_PIX, y0+CELL_PIX
                t = self.layout[(x,y)]
                if t == CELL_SIGNAL:
                    bg = "#fff8dc"  # light yellow
                elif t == CELL_ROAD:
                    bg = "#f0f0f0"  # gray
                elif t == CELL_HEAVY:
                    bg = "#ffe4e1"  # light pink
                else:
                    bg = "#8b0000"  # dark red
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=bg, outline="black")
                # label
                self.canvas.create_text(x0+6, y0+6, anchor="nw", text=f"{x},{y}", font=("Arial",8))
                # show cell type short label
                self.canvas.create_text(x0+CELL_PIX-6, y0+6, anchor="ne", text=t[:4], font=("Arial",8))
                # draw queue bar
                q = self.grid_state.queues[(x,y)]
                # map q to bar width
                bw = min(CELL_PIX-12, int((q/60.0) * (CELL_PIX-12)))
                self.canvas.create_rectangle(x0+6, y0+CELL_PIX-12, x0+6+bw, y0+CELL_PIX-6, fill="gray")
                # draw signal if exists
                if (x,y) in self.signals:
                    sig = self.signals[(x,y)]
                    color = "green" if sig.state=="GREEN" else "red"
                    self.canvas.create_oval(x0+CELL_PIX//2-10, y0+CELL_PIX//2-10, x0+CELL_PIX//2+10, y0+CELL_PIX//2+10, fill=color)
        # draw ambulance
        ax, ay = self.ambulance.pos
        ax0, ay0 = ax*CELL_PIX+CELL_PIX//6, ay*CELL_PIX+CELL_PIX//6
        ax1, ay1 = ax0 + CELL_PIX//1.5, ay0 + CELL_PIX//1.5
        self.canvas.create_rectangle(ax0, ay0, ax1, ay1, fill="blue")
        # draw start and goal markers
        sx, sy = self.ambulance.start
        gx, gy = self.ambulance.goal
        self.canvas.create_text(sx*CELL_PIX + CELL_PIX//2, sy*CELL_PIX+4, text="START", fill="black", font=("Arial",10,"bold"))
        self.canvas.create_text(gx*CELL_PIX + CELL_PIX//2, gy*CELL_PIX+4, text="GOAL", fill="black", font=("Arial",10,"bold"))
        # draw server status box
        self.canvas.create_rectangle(6, WINDOW_HEIGHT-90, 200, WINDOW_HEIGHT-6, fill="#f8f8ff", outline="black")
        self.canvas.create_text(12, WINDOW_HEIGHT-84, anchor="nw", text=f"AI Last decision: {len(self.server.log)}", font=("Arial",9))
        # show ambulance stats in info textbox
        self.info.delete("1.0", "end")
        self.info.insert("end", f"Time: {int(self.ambulance.travel_time):d}\n")
        self.info.insert("end", f"Amb pos: {self.ambulance.pos}  idx:{self.ambulance.curr_index}\n")
        self.info.insert("end", f"Estimated path len: {len(self.ambulance.path)}\n")
        self.info.insert("end", f"Blocking: {self.ambulance.blocking_time:.1f}s\n")
        self.info.insert("end", f"Server decisions: {len(self.server.log)}\n")
        self.info.insert("end", f"Signals Count: {len(self.signals)}\n")
        if self.server.log:
            last = self.server.log[-1]
            self.info.insert("end", f"Last action: {last.get('note','')}\nTime: {time.strftime('%H:%M:%S', time.localtime(last['time']))}\n")

    def step_simulation(self):
        # single simulation step: update grid, sensors, server decisions, ambulance
        dt = SIM_SPEED
        # 1) traffic arrivals
        self.grid_state.step_traffic_arrivals()
        # 2) sensors report periodically (synchronously here)
        reports = self.server.receive_sensor_reports()

        # 3) server optionally clears overrides when enough time passed
        self.server.clear_overrides_after(seconds=6)

        # 4) ambulance step (requests preemption inside)
        self.ambulance.step(dt=dt)

        # 5) apply draining at green signals: signals that are GREEN allow some vehicles to pass
        for pos, sig in self.signals.items():
            if sig.state == "GREEN":
                drained = self.grid_state.drain_queue(pos, count=4)
                # log drained event occasionally
                if drained > 0:
                    self.log_rows.append((time.time(), "drain", pos, drained))
        # also locally advance uncontrolled signals' timers
        for pos, sig in self.signals.items():
            sig.step_timer(dt=dt)

        # 6) server may make decisions (simple periodic polling)
        # emulate decision loop: when ambulance within 4 cells of a signal, server decides
        if not self.ambulance.completed:
            # find next hops on ambulance path
            path = self.ambulance.path
            if len(path) > 1:
                # current corridor = next 3 nodes
                idx = self.ambulance.curr_index
                corridor = path[idx: idx+4]
                # compute ETA for corridor
                eta = self.server.predict_eta(corridor, self.ambulance.pos)
                if eta < PREDICTION_HORIZON:
                    # issue preemption (runs quick)
                    self.server.issue_preemption(self.ambulance.pos, path, severity=self.ambulance.severity)
        # 7) log step
        self.log_rows.append((time.time(), "step", self.ambulance.pos, dict(self.grid_state.queues)))
        # 8) update GUI drawing
        self.draw()

    def _run_loop(self):
        if not self.running:
            return
        # step simulation
        self.step_simulation()
        # check termination
        if self.ambulance.completed:
            self.status_text.set("Ambulance Arrived")
            # write logs to CSV and print short summary
            self.save_logs()
            self.running = False
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.reset_btn.config(state="normal")
            return
        # schedule next
        after_ms = max(50, int(UPDATE_MS / max(0.2, SIM_SPEED)))
        self._after_id = self.root.after(after_ms, self._run_loop)

    def save_logs(self):
        # Save self.log_rows and server.log to CSV for inspection
        print("[SIM] Saving logs to", LOG_CSV)
        rows = []
        for item in self.log_rows:
            tstamp = item[0]
            kind = item[1]
            pos = item[2]
            if kind == "drain":
                rows.append({"time": tstamp, "event": "drain", "pos": str(pos), "value": item[3]})
            elif kind == "step":
                rows.append({"time": tstamp, "event": "step", "pos": str(pos), "queues_sample": str(item[3])})
        # server decisions
        for d in self.server.log:
            rows.append({"time": d["time"], "event": "decision", "pos": str(d.get("ambulance_pos")), "value": d.get("note")})
        df = pd.DataFrame(rows)
        df.to_csv(LOG_CSV, index=False)
        self.info.insert("end", f"Logs saved to {LOG_CSV}\n")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    gui = MT_GUI(root)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.mainloop()
