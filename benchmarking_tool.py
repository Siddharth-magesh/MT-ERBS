import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
from matplotlib.backends.backend_pdf import PdfPages

# ----------------------------
# City + Simulation Parameters
# ----------------------------
CITY_SIZE = 5
SIM_TIME = 600         # longer simulation
RUNS = 15              # more runs for stable stats
QUEUE_CAPACITY = 30
AMBULANCE_OD = ((0,0), (4,4))

# ----------------------------
# Traffic Signal Class
# ----------------------------
class TrafficSignal:
    def __init__(self, node):
        self.node = node
        self.phase = 0
        self.timer = 0
        self.green_time = 5
        self.red_time = 5
        self.switches = 0

    def step(self):
        self.timer += 1
        if self.phase == 0 and self.timer >= self.green_time:
            self.phase = 1
            self.timer = 0
            self.switches += 1
        elif self.phase == 1 and self.timer >= self.red_time:
            self.phase = 0
            self.timer = 0
            self.switches += 1

# ----------------------------
# Simulation Environment
# ----------------------------
class TrafficNetwork:
    def __init__(self, size, seed, stress=False, blockage=False):
        random.seed(seed)
        np.random.seed(seed)
        self.size = size
        self.signals = { (i,j): TrafficSignal((i,j)) for i in range(size) for j in range(size)}
        self.queues = defaultdict(int)
        self.total_delay = 0
        self.spillbacks = 0
        self.throughput = 0
        self.stress = stress
        self.blockages = set()
        if blockage:
            # randomly block a few intersections
            self.blockages = {(random.randint(0,size-1), random.randint(0,size-1)) for _ in range(3)}

    def arrivals(self):
        lam = 4 if self.stress else 2  # stress scenario doubles arrival rate
        for node in self.signals:
            if node in self.blockages:
                continue
            self.queues[node] += np.random.poisson(lam)
            if self.queues[node] > QUEUE_CAPACITY:
                self.spillbacks += 1
                self.queues[node] = QUEUE_CAPACITY

    def departures(self, ambulance_nodes=None):
        for node, signal in self.signals.items():
            if node in self.blockages:
                continue
            if ambulance_nodes and node in ambulance_nodes:
                outflow = min(5, self.queues[node])
            else:
                outflow = min(2 if signal.phase == 0 else 0, self.queues[node])
            self.queues[node] -= outflow
            self.throughput += outflow
            self.total_delay += self.queues[node]
            signal.step()

# ----------------------------
# Ambulance Simulation
# ----------------------------
def simulate(run_id, strategy):
    stress = (strategy == "StressTest")
    blockage = (strategy == "Blockages")
    net = TrafficNetwork(CITY_SIZE, seed=run_id, stress=stress, blockage=blockage)

    amb_pos = AMBULANCE_OD[0]
    target = AMBULANCE_OD[1]
    travel_time = 0
    blocking_time = 0
    amb_path = []

    log_rows = []

    for t in range(SIM_TIME):
        net.arrivals()
        amb_nodes = [amb_pos] if strategy in ["MT_ERBS","StressTest","Blockages"] else None
        net.departures(ambulance_nodes=amb_nodes)

        # ambulance moves every 5 steps if not arrived
        if t % 5 == 0 and amb_pos != target:
            i,j = amb_pos
            if i < target[0]: i+=1
            elif j < target[1]: j+=1
            amb_pos = (i,j)
            amb_path.append(amb_pos)

        if net.queues[amb_pos] > 0:
            blocking_time += 1

        travel_time = t
        if amb_pos == target:
            break

        log_rows.append({
            "time": t,
            "ambulance_pos": amb_pos,
            "blocking": net.queues[amb_pos],
            "total_delay": net.total_delay,
            "spillbacks": net.spillbacks,
            "avg_queue": np.mean(list(net.queues.values())),
            "throughput": net.throughput
        })

    metrics = {
        "travel_time": travel_time,
        "blocking_time": blocking_time,
        "avg_delay": net.total_delay / SIM_TIME,
        "spillbacks": net.spillbacks,
        "switches": sum(s.switches for s in net.signals.values()) / len(net.signals),
        "avg_queue_length": np.mean(list(net.queues.values())),
        "p95_delay": np.percentile([r["total_delay"] for r in log_rows],95) if log_rows else 0,
        "ambulance_arrival_success": int(amb_pos==target),
        "throughput": net.throughput
    }
    return metrics, pd.DataFrame(log_rows)

# ----------------------------
# Run Benchmark
# ----------------------------
def run_benchmark():
    strategies = ["Baseline","MT_ERBS","StressTest","Blockages"]
    results, logs = {s:[] for s in strategies}, {s:[] for s in strategies}

    for run in range(RUNS):
        for strat in strategies:
            metrics, logdf = simulate(run, strat)
            metrics["run"] = run
            results[strat].append(metrics)
            logdf.to_csv(f"{strat}_Run{run}.csv", index=False)
            logs[strat].append(logdf)
            print(f"Run {run}, {strat}: {metrics}")

    # save Excel
    with pd.ExcelWriter("benchmark_results.xlsx") as writer:
        for strat in strategies:
            pd.DataFrame(results[strat]).to_excel(writer, sheet_name=f"{strat}_Metrics", index=False)

        summary = []
        for strat, vals in results.items():
            df = pd.DataFrame(vals)
            means, stds = df.mean(numeric_only=True), df.std(numeric_only=True)
            for col in means.index:
                summary.append({"Strategy": strat, "Metric": col, "Mean": means[col], "Std": stds[col]})
        pd.DataFrame(summary).to_excel(writer, sheet_name="AggregateSummary", index=False)

        for strat in logs:
            all_runs = pd.concat(logs[strat], keys=range(RUNS))
            avg = all_runs.groupby("time").mean(numeric_only=True)
            avg.to_excel(writer, sheet_name=f"{strat}_AvgTimeSeries")

    # text report
    with open("benchmark_report.txt","w") as f:
        f.write("Benchmark Results (Mean ± Std)\n")
        f.write("="*50+"\n")
        for strat, vals in results.items():
            df = pd.DataFrame(vals)
            f.write(f"\nStrategy: {strat}\n")
            for col in ["travel_time","blocking_time","avg_delay","spillbacks","switches","avg_queue_length","p95_delay","throughput"]:
                f.write(f"{col}: {df[col].mean():.2f} ± {df[col].std():.2f}\n")
            f.write(f"Arrival success rate: {df['ambulance_arrival_success'].mean()*100:.1f}%\n")

    # plots
    pdf = PdfPages("benchmark_plots.pdf")
    def save_plot(fig,name):
        fig.savefig(f"{name}.png")
        pdf.savefig(fig)
        plt.close(fig)

    # metric boxplots
    for metric in ["travel_time","avg_delay","spillbacks","blocking_time","throughput"]:
        fig = plt.figure(figsize=(8,6))
        data = [pd.DataFrame(results[s])[metric] for s in strategies]
        plt.boxplot(data, labels=strategies)
        plt.title(metric)
        save_plot(fig,f"{metric}_boxplot")

    # timeseries
    for strat in logs:
        avg = pd.concat(logs[strat], keys=range(RUNS)).groupby("time").mean(numeric_only=True)
        for metric in ["blocking","avg_queue","throughput"]:
            fig = plt.figure(figsize=(8,6))
            plt.plot(avg.index, avg[metric], label=f"{strat} mean")
            plt.title(f"{metric} over time ({strat})")
            plt.legend()
            save_plot(fig,f"{metric}_{strat}_timeseries")

    pdf.close()

if __name__ == "__main__":
    run_benchmark()
