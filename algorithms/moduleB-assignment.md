### Module B — Mission Assignment and Hospital Targeting

```
FUNCTION ASSIGN_OR_UPDATE_AMBULANCE(req, AMB, HOSP):
  C ← CANDIDATE_AMBULANCES_NEAR(req.loc, AMB)
  a* ← ARGMAX_{a∈C} SCORE_ASSIGNMENT(a, req, HOSP)     # proximity, fuel/health, ETA
  req.target_hospital ← SELECT_HOSPITAL(req, HOSP)     # capacity, specialty, distance
  return a*
```