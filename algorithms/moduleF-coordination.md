### Module F — Public, Hospital, and Law Enforcement Coordination

```
FUNCTION BROADCAST_NAV_ADVISORIES(NAV, P):
  NAV.push_diversion_messages(corridor=P, radius=R, ttl=T)

FUNCTION NOTIFY_HOSPITAL(HOSP, req, ETA):
  HOSP[req.target_hospital].prep(incident=req, eta=ETA)

FUNCTION REQUEST_ESCORT_OR_CONTRAFLOW(POLICE, node_or_edge):
  POLICE.dispatch(node_or_edge)

FUNCTION CITY_RADIO_INTERRUPT(msg, dur ≤ 30s):
  RADIO.broadcast(msg, duration=dur)
```