### Module C — Time-Dependent Route Planning with MPC Refinement

```
FUNCTION PLAN_ROUTE_WITH_CONSTRAINTS(G, s_t, src, dst, POL):
  # Create augmented graph with reversible lanes/contraflow permitted by policy
  G' ← AUGMENT_GRAPH_WITH_REVERSIBLE(G, POL)

  # Base weights include predicted effect of manipulation (green wave benefit)
  W_e ← ETA_MODEL.EDGE_WEIGHTS(G', s_t)

  P0 ← TIME_DEPENDENT_SHORTEST_PATH(G', src, dst, W_e)

  # Receding-horizon refinement (local search over neighbors, horizon H)
  P ← P0
  for k = 1..K:
     ŝ ← FORECAST(s_t, horizon=H)
     obj(P) = ETA(P | ŝ) + λ1*NETWORK_SPILLBACK(P | ŝ) + λ2*SWITCH_COST(P)
     P ← LOCAL_NEIGHBOR_IMPROVEMENT(P, obj, constraints=POL)
  return P
```