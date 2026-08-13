# Event Processing Requirements

## Functional Requirements

- WHEN the sensor detects motion AND WHEN the alarm is armed, THE System SHALL trigger the siren within 2 seconds.
- WHILE the database is in maintenance mode AND WHILE the backup job is active, THE System SHALL queue all incoming write requests.
- IF the user has two-factor authentication enabled AND IF the session token has expired, THEN THE System SHALL redirect to the login page.
- WHEN the order total exceeds $500, WHEN the customer is flagged for review, THE System SHALL hold the order for manual approval.
- WHILE network latency exceeds 200ms, THE System SHALL switch to the local cache for all read operations.
- WHERE the deployment region is ap-southeast-1, WHERE compliance tier is SOC2, THE System SHALL encrypt data at rest using AES-256.
- WHEN the user indicates that IF a cancellation occurs within 24 hours THEN a refund is expected, THE System SHALL log the preference.
- WHILE the system is in degraded mode, WHEN a priority-1 ticket arrives, THE System SHALL escalate to the on-call engineer immediately.
- IF the temperature reading is above 85°C AND WHILE the fan speed is below 3000 RPM, THEN THE System SHALL trigger a thermal alert.
- WHEN the batch job completes, IF any records failed validation, THEN THE System SHALL generate an exception report within 60 seconds.
