### Module H — Incident, Closure, and Special Case Handling

```
EVENT ON_INCIDENT_OR_CLOSURE(edge e or node i):
  MARK_BLOCKED(e or i)
  if ALT_EXISTS(e): REROUTE_AFFECTED_CORRIDORS(e)
  else if POL.reversible_allowed(e) and CONTRAFLOW_PERMITTED(e):
       REQUEST_ESCORT_OR_CONTRAFLOW(POLICE, e); OPEN_REVERSIBLE_LANE(SIG, e)
  DISPATCH_CLEARANCE_TEAM(e or i)

# Camera-autonomous trigger
FUNCTION CAMERA_AUTONOMOUS_INITIATION(z_cam):
  if VISION.detects_serious_accident(z_cam):
     req ← AUTO_CREATE_REQUEST(location, severity, type)
     REGISTER_REQUEST(req)
     CALL_NEAREST_CONTACT_FOR_VERIFICATION(req)   # Aadhaar/ID-backed if available
```