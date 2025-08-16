### Module G — Multi-Ambulance Deconfliction

```
FUNCTION RESOLVE_MULTI_CORRIDOR_CONFLICTS(POL):
  R ← ACTIVE_CORRIDORS()
  if |R| ≤ 1: return

  # Priority ordering by severity, clinical urgency, and time-to-hospital
  ORDER ← SORT(R, key = (-SEVERITY, ETA_TO_HOSPITAL, HOSPITAL_CAPACITY_MARGIN))

  for i in 1..|ORDER|:
    for j in i+1..|ORDER|:
      if CONFLICTS(ORDER[i], ORDER[j]):
         if CAN_TIME_SHIFT(ORDER[j], Δt ≤ POL.max_time_shift_between_corridors):
            OFFSET_GREEN_WAVE(ORDER[j], Δt)
         else if ALT_ROUTE_EXISTS(ORDER[j]):
            ORDER[j] ← REROUTE_CORRIDOR(ORDER[j])
         else
            REQUEST_ESCORT_OR_CONTRAFLOW(POLICE, CONFLICT_NODES(ORDER[i], ORDER[j]))
```