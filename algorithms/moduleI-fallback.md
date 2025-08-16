### Module I — Fallbacks, Fail-Safe, and Post-Event Normalization

```
FUNCTION APPLY_RULE_BASED_PREEMPTION(SIG, POL):
  # Conservative green wave with fixed upstream gating quotas
  for node in CRITICAL_INTERSECTIONS():
     SIG.preempt(node, plan=FIXED_EMERGENCY_PROFILE(POL))

FUNCTION APPLY_FAILSAFE_PLANS(SIG):
  for node in ALL_INTERSECTIONS():
     SIG.load_plan(node, plan=LOCAL_FAILSAFE_TIMINGS())

FUNCTION NORMALIZE_AND_REBALANCE(P, POL):
  for node in INTERSECTIONS(P):
     EXTRA_GREEN_TO_DELAYED_APPROACHES(node, quota=ADAPTIVE_FAIRNESS())
     RESET_LED_PANEL(node)
  NOTIFY_NAV_CLEAR(P)
```