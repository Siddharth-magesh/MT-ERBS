# Benchmarking Tool for MT-ERBS

This tool (`benchmarking_tool.py`) is the core evaluation engine of the MT-ERBS project. It simulates a city grid with signals, vehicles, and an ambulance navigating from source to destination.

---

## Features

- **City Simulation**  
  - 5x5 to larger grids of intersections  
  - Poisson-distributed traffic arrivals  
  - Queue management with spillback limits  

- **Ambulance Priority (MT-ERBS)**  
  - Clears signals along ambulance path  
  - Manipulates upstream and downstream flows  
  - Reduces ambulance travel delays  

- **Benchmarking**  
  - Runs multiple seeds for statistical confidence  
  - Exports per-run CSVs with time-series metrics  
  - Aggregates into a single Excel summary file  

- **Visualization**  
  - Boxplots for ambulance travel time, average delay, spillbacks  
  - Saved automatically into `/benchmarks/images/`

---

## Outputs

1. CSV logs for each run (`Baseline_metrics.csv`, `MT_ERBS_metrics.csv`)  
2. Excel Summary (`benchmark_summary.xlsx`) with aggregated mean ± std  
3. Images: boxplots for benchmarking metrics  
4. Logs: detailed run information under `/logs`

---

## Running the Tool

```bash
uv sync
uv run benchmarking_tool.py
```

Outputs will be saved under `/benchmarks/` and `/logs`.

---

## Evaluation Metrics

- Ambulance Travel Time: Total time to reach destination  
- Blocking Delay: Time ambulance is obstructed  
- Average Vehicle Delay: Mean queue length across city  
- Spillbacks: Number of overflows beyond queue capacity  
- Signal Switches: Average switching cycles per signal  

---

## Notes

- Parameters like grid size, simulation time, and runs can be tuned inside the file.  
- Current defaults: `CITY_SIZE=5`, `SIM_TIME=1000`, `RUNS=20`.  
- Results are deterministic per random seed.
