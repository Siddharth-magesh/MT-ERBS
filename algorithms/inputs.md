### Global Inputs, State, and Policies

```
INPUTS / RESOURCES
  G(V,E): Directed road graph with intersections S ⊆ V and approaches A(i) per node i
  SIG: Field signal controller API (set_phase, set_split, preempt, reversible_lane)
  CAM: Citywide camera streams; edge detection at junctions (counts, classes, incidents)
  AMB: Ambulance fleet telemetry {id, position, velocity, health, fuel}
  HOSP: Hospital endpoints {capacity, specialty, triage state}
  POLICE: Dispatch endpoint for escorts / contraflow authorization
  NAV: Navigation providers (public advisory API), Transit Ops, City Radio
  MAP: Static topology, lane configs, reversible-lane flags, ped phases
  CLOSURES: Planned works; dynamically updated incidents/closures

SAFETY & POLICY CONSTRAINTS
  POL: {
    g_min, g_max, intergreen, ped_clear, max_hold,
    max_queue_storage(i, a), reversible_allowed(e), contraflow_permitted(e),
    fairness_quota_non_corridor, max_time_shift_between_corridors,
    vip_threshold, severity_weights
  }

SYSTEM STATE (updated each cycle t)
  s_t = {
    queues q_i,a(t), phase_i(t), occupancy_i,a(t), incidents, closures,
    weather/visibility tags, forecast ŝ_{t+Δ}
  }

LEARNING MODELS
  NLP_CALL: Call intake → {severity σ ∈ [0,1], type, geoloc}
  VISION: Per-junction multi-task: ambulance detection, class counts, queues, incidents
  ETA_MODEL: Edge travel time estimator with effect-of-manipulation features
  FORECAST: Short-horizon traffic forecaster (TCN/LSTM/Transformer)
```