mermaid
flowchart LR
CAM[Camara RTSP/Video] --> CW[CameraWorker]
CW --> FR[Frame]
FR --> MN[MoveNet]
MN --> KP[Keypoints]
KP --> TR[CentroidTracker<br/>client_id]
TR --> SPM[SessionPersonManager<br/>athlete_X]
SPM --> SD[SquatDetector]
SD --> EV[SquatEventAggregator]
EV --> WS[WebSocket Server]
WS --> UI[Frontend UI]
UI --> WB[WorkoutBoard / ReviewView]
