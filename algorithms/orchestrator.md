### Orchestrator (10 Hz control loop)

```
ALGORITHM MT_ERBS_MAIN()
  while TRUE:
    # 1) Perception & Fusion
    calls  ← RECEIVE_NEW_CALLS()
    for c in calls:
       req ← NLP_CALL(c)                                # {loc, type, severity σ}
       REGISTER_REQUEST(req)

    z_cam ← PROCESS_CAMERAS(CAM)                        # detect queues/incidents/ambulances
    s_t   ← FUSE_STATE(z_cam, CLOSURES, SIG_PHASES(), AMB_TELEMETRY())

    # 2) Assign/Update Missions
    for req in ACTIVE_REQUESTS():
       a ← ASSIGN_OR_UPDATE_AMBULANCE(req, AMB, HOSP)
       if a = ∅: continue

       # 3) Plan Corridor (routing + constraints)
       P ← PLAN_ROUTE_WITH_CONSTRAINTS(G, s_t, a.position, req.target_hospital, POL)

       # 4) Build Signal Plan: Green Wave + Upstream Gating
       SCHED ← BUILD_SIGNAL_PLAN(P, s_t, POL)

       # 5) Field Actuation + Public/Institutional Coordination
       APPLY_SIGNAL_PLAN(SIG, SCHED)
       SET_EMERGENCY_INDICATORS(P)                      # LEDs/boards
       BROADCAST_NAV_ADVISORIES(NAV, P)                 # diversions
       NOTIFY_HOSPITAL(HOSP, req, ETA=ESTIMATE_ETA(P))
       IF req.severity ≥ POL.vip_threshold: NOTIFY(POLICE, req)

    # 6) Multi-Ambulance Deconfliction (time-shifts, alt corridors, escort)
    RESOLVE_MULTI_CORRIDOR_CONFLICTS(POL)

    # 7) Fallbacks and Health Checks
    if AI_DEGRADED():   APPLY_RULE_BASED_PREEMPTION(SIG, POL)
    if CORE_DOWN():     APPLY_FAILSAFE_PLANS(SIG); ALERT_MANUAL_CONTROL(POLICE)

    # 8) Post-Event Normalization
    for p in COMPLETED_CORRIDORS():
       NORMALIZE_AND_REBALANCE(p, POL)

  end while
```