### Module E — Field Actuation & Indicators

```
FUNCTION APPLY_SIGNAL_PLAN(SIG, SCHED):
  for node, plan in SCHED:
     SIG.set_phase_plan(node, plan.main_window, plan.non_corridor_bursts)
  return

FUNCTION SET_EMERGENCY_INDICATORS(P):
  for node in INTERSECTIONS(P):
     ACTIVATE_LED_EMERGENCY_PANEL(node, symbol="RED_CROSS")
```