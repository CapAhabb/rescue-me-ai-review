CREATE TABLE IF NOT EXISTS escalation_policies (
  id TEXT PRIMARY KEY,
  heartbeat_late_after_s INTEGER NOT NULL,
  contact_degraded_after_s INTEGER NOT NULL,
  user_warning_after_s INTEGER NOT NULL,
  contact_notification_after_s INTEGER NOT NULL,
  incident_pending_after_s INTEGER NOT NULL,
  emergency_active_after_s INTEGER NOT NULL,
  responder_handoff_after_s INTEGER NOT NULL,
  low_battery_percent INTEGER NOT NULL,
  off_route_grace_s INTEGER NOT NULL,
  no_user_response_s INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  owner_contact TEXT NOT NULL,
  created_at TEXT NOT NULL,
  activated_at TEXT,
  resolved_at TEXT,
  cancelled_at TEXT,
  FOREIGN KEY (policy_id) REFERENCES escalation_policies(id)
);

CREATE TABLE IF NOT EXISTS emergency_contacts (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  label TEXT NOT NULL,
  email TEXT NOT NULL,
  is_default_responder INTEGER NOT NULL DEFAULT 0,
  acknowledgment_state TEXT NOT NULL DEFAULT 'PENDING',
  acknowledged_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS float_plan_legs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  start_latitude REAL NOT NULL,
  start_longitude REAL NOT NULL,
  end_latitude REAL NOT NULL,
  end_longitude REAL NOT NULL,
  corridor_radius_m REAL NOT NULL,
  min_speed_mps REAL,
  max_speed_mps REAL,
  heading_tolerance_deg REAL,
  checkpoint_due_at TEXT,
  stop_tolerance_s INTEGER,
  timing_tolerance_s INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, sequence),
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS telemetry_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  device_id TEXT NOT NULL,
  device_sequence INTEGER NOT NULL,
  observed_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  gps_accuracy_m REAL NOT NULL,
  speed_mps REAL,
  course_deg REAL,
  heading_deg REAL,
  battery_percent REAL,
  network_state TEXT NOT NULL,
  provenance TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  raw_payload_json TEXT NOT NULL,
  duplicate_of TEXT,
  UNIQUE(session_id, device_id, device_sequence),
  FOREIGN KEY (session_id) REFERENCES sessions(id),
  FOREIGN KEY (duplicate_of) REFERENCES telemetry_events(id)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_session_observed
  ON telemetry_events(session_id, observed_at);

CREATE TABLE IF NOT EXISTS drift_forecasts (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  environmental_provenance_json TEXT NOT NULL,
  datum_json TEXT NOT NULL,
  datum_uncertainty_json TEXT NOT NULL,
  object_profile_json TEXT NOT NULL,
  horizon_minutes INTEGER NOT NULL,
  confidence_contours_json TEXT NOT NULL,
  assumptions_json TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_drift_forecasts_session_created
  ON drift_forecasts(session_id, created_at);

CREATE TABLE IF NOT EXISTS incident_share_tokens (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  contact_id TEXT,
  token_hash TEXT NOT NULL UNIQUE,
  scope TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  revoked_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions(id),
  FOREIGN KEY (contact_id) REFERENCES emergency_contacts(id)
);

CREATE TABLE IF NOT EXISTS incident_share_access_logs (
  id TEXT PRIMARY KEY,
  token_id TEXT,
  accessed_at TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  outcome TEXT NOT NULL,
  FOREIGN KEY (token_id) REFERENCES incident_share_tokens(id)
);

CREATE TABLE IF NOT EXISTS session_transition_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  from_state TEXT NOT NULL,
  to_state TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS ai_advisories (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  advisory_text TEXT NOT NULL,
  supporting_evidence_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  accepted_for_escalation INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_ai_advisories_session_created
  ON ai_advisories(session_id, created_at);
