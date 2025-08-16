# Manipulating Traffic for Effective Rescue by Bypassing the Signals (MT-ERBS)

This repository contains our AI-driven approach to intelligent traffic management, designed to prioritize ambulances during emergencies by dynamically manipulating traffic signals. Using simulation, benchmarking, and visual demonstration, the system evaluates strategies to reduce ambulance travel time, minimize traffic delays, and ensure effective rescue operations.

---

## Repository Structure

```
.
├── benchmarking_tool.py        # Core benchmarking simulator
├── benchmarking_tool_README.md # Documentation for benchmarking tool
├── /benchmarks
│   ├── benchmark_summary.xlsx  # Aggregated results
│   ├── Baseline_metrics.csv    # Per-run baseline logs
│   ├── MT_ERBS_metrics.csv     # Per-run MT-ERBS logs
│   ├── images/                 # Generated graphs, boxplots, etc.
│   └── videos/                 # Benchmarking demo videos
├── /logs
│   ├── run_logs.txt            # Detailed execution logs
│   └── per_run_csvs/           # Time-series logs for each run
├── /gui_demo
│   ├── gui_demo.py             # Minimal GUI demonstration of traffic grid
│   └── gui_assets/             # Icons, maps, or supporting files
└── README.md                   # Main project README
```

---

## Features

- **Benchmarking Tool** (`benchmarking_tool.py`)  
  Simulates a grid city, traffic signals, and ambulance routes under different strategies (Baseline vs. MT-ERBS).  
  Produces logs, Excel summaries, and graphs for detailed evaluation.  

- **Visualization**  
  Generates boxplots for travel time, vehicle delays, and spillbacks, stored under `/benchmarks/images/`.

- **Logs**  
  Complete time-series outputs of queues, delays, and ambulance states are stored in `/logs`.

- **Minimal GUI** (`gui_demo.py`)  
  A simple top-down map demo showing signals, roads, blockages, and ambulance movements with AI/IoT-inspired logic.

- **Benchmarking Media**  
  Videos and images of two test cases demonstrating system performance under different traffic conditions.

---

## Benchmarking

- **Test Case 1 & 2**: Six images (three per case) are provided to illustrate system response.  
- **Video Demos**: Linked in `/benchmarks/videos/` for live visualization of ambulance prioritization.  
- **Metrics Evaluated**:
  - Ambulance travel time  
  - Blocking delay  
  - Average traffic delay  
  - Signal switching patterns  
  - Spillback frequency  

---

## How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/Siddharth-magesh/MT-ERBS.git
   cd mt-erbs
   ```

2. Run the benchmarking tool:
   ```bash
   uv sync
   uv run benchmarking_tool.py
   ```

3. View outputs in:
   - `/benchmarks/` → Graphs, Excel summary, metrics  
   - `/logs/` → Detailed time-series logs  
   - `/gui_demo/` → Run `python gui_demo.py` for the minimal GUI demo  

---

## Media

- Benchmarking graphs: see `/benchmarks/images/`  
- Simulation videos: see `/benchmarks/videos/`  

---

## Papers & Documentation

- Abstract, Introduction, Related Works, Discussion, Future Works, Conclusion are all included in this repo for reference alongside the implementation.

---

## Conclusion

MT-ERBS demonstrates how AI-driven traffic signal manipulation can reduce ambulance delays and improve rescue efficiency, validated via benchmarking and simulation under varying conditions.
