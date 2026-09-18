# Architecture

The frontend is a responsive React/Vite single-page application. FastAPI exposes validated JSON endpoints. At startup the backend deterministically seeds `backend/data/campus_demo.db` with simulated resource records. In-memory analysis uses the same deterministic seed to keep the prototype simple and repeatable.

The system has no authentication, real IoT connection or external AI requirement. CORS is limited to the local Vite URLs.

## Analysis method

Records are grouped by resource type and location. The average of the latest four days is compared to the preceding period. A group is flagged when the recent average rises 12% or more, or when a reading exceeds 125% of baseline. The API returns observed value, baseline, percentage difference and the reason.
