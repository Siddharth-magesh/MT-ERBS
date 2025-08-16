### Module A — Perception, Fusion, and Forecasting

```
FUNCTION FUSE_STATE(z_cam, closures, phases, amb_telemetry):
  s ← INIT_STATE()
  s.queues, s.occupancies ← EXTRACT_FROM(z_cam)
  s.incidents ← DETECT_INCIDENTS(z_cam) ∪ closures
  s.phases ← phases
  s.ambulances ← MAP_MATCH(amb_telemetry, MAP)
  s.weather ← ESTIMATE_WEATHER(z_cam)
  ŝ ← FORECAST(s)                              # short-horizon state for scheduling alignment
  return MERGE(s, ŝ)
```