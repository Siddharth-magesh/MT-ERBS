### Module D — Signal Plan Construction (Green Wave + Complementary Upstream Gating)

```
FUNCTION BUILD_SIGNAL_PLAN(P, s_t, POL):
  # Arrival predictions along corridor
  ETA_node ← ESTIMATE_ARRIVALS_ALONG(P, s_t)

  SCHED ← {}
  # 1) Main-corridor alignment (green windows)
  for node in INTERSECTIONS(P):
     window ← ALIGN_GREEN_TO_ARRIVAL(ETA_node[node], POL.g_min, POL.g_max, POL.intergreen)
     SCHED[node].main_window ← window

  # 2) Complementary (upstream/prior) signal management  ← EXPLICIT MODULE
  COMP ← IDENTIFY_UPSTREAM_COMPLEMENTARIES(P, MAP)    # DAG of feeder signals
  for comp in TOPOLOGICAL_ORDER(COMP):
     # Eternal Hold: brief prevention of over-saturation on feeder approaches
     HOLD(comp, duration ≤ POL.max_hold)
     # Throttle inflow by quota; release short bursts to avoid starvation
     THROTTLE(comp, quota = POL.fairness_quota_non_corridor)
     # Ensure downstream storage not exceeded
     ENFORCE_STORAGE(comp, max_queue_storage(comp))

  # 3) Non-corridor fairness at corridor nodes
  for node in INTERSECTIONS(P):
     SCHED[node].non_corridor_bursts ← TIMED_RELEASES(node, POL.fairness_quota_non_corridor)

  # 4) Pedestrian safety and inter-greens
  for node in INTERSECTIONS(P):
     APPLY_PEDESTRIAN_CLEARANCE(SCHED[node], POL.ped_clear, POL.intergreen)

  return SCHED
```