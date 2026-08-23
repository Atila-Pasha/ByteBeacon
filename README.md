# ByteBeacon

ByteBeacon is an open-source API and uptime monitoring platform for developers.

It continuously checks your APIs and web services, tracks their availability and response time, and helps you detect downtime and service incidents.

> ByteBeacon is currently under active development.

## Running monitors in production

Run the scheduler in exactly one process or deployment replica. Set
`SCHEDULER_ENABLED=false` on API-only replicas, and enable it only for the
dedicated monitoring worker. Otherwise every replica checks every monitor and
creates duplicate check records.
