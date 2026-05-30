# SmartRescue AI — Backend Service

Welcome to the backend service of **SmartRescue AI**, a production-grade, AI-powered road accident emergency response ecosystem. This backend facilitates secure, real-time coordination between **Travellers**, **Ambulance Drivers**, and **Hospitals** during critical road emergencies.

---

## 🚀 Key Features

*   **AI Accident Detection:** Analyzes streams of high-frequency sensor readings (accelerometer, gyroscope, speed, orientation, heart rate) using a trained **RandomForest model**. Includes:
    *   Multi-threshold confidence score logic (auto-trigger vs confirmation required).
    *   False-alarm filtering with a temporal sliding window buffer.
*   **Real-time Real-world Dispatch:** Employs GPS coordinate logic (Haversine formula) to locate the closest available, verified ambulances.
*   **Automatic Reassignment Loop:** If an assigned ambulance rejects an emergency, the system automatically recalibrates and alerts the next closest driver.
*   **Paramedic updates to Hospital:** Live updates (oxygen needed, blood type, ICU beds, vital signals) are streamed en-route from the ambulance directly to surgeons and doctors.
*   **WebSocket Real-time Channels:** Seamless two-way data streaming for live vehicle tracking, hospital dashboards, and active incident timeline feeds.
*   **Enterprise-Grade Security:** Firebase Authentication token parsing coupled with secure, role-based internal JSON Web Tokens (JWT) and slowapi rate limiting.
*   **Chronological Auditing:** Complete history of all transactional actions stored securely in a dedicated audit log collection.

---

## 🛠️ Tech Stack

*   **Framework:** FastAPI (Python 3.10+)
*   **Realtime/Sockets:** Standard WebSockets (FastAPI integration)
*   **Database:** Firebase Firestore (NoSQL Document database)
*   **Auth:** Firebase Auth + Custom JWT (python-jose)
*   **Push Notifications:** Firebase Cloud Messaging (FCM)
*   **Machine Learning:** Joblib (RandomForest Classifier) + Scikit-Learn

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── auth/              # JWT tokens, custom RBAC middlewares, and Firebase verification
│   ├── config/            # Central settings configuration (BaseSettings)
│   ├── firebase/          # Firestore DB operations and FCM push notifications
│   ├── ml/                # RandomForest predictor, confidence levels, and sliding buffer
│   ├── models/            # Pydantic schemas for data validation
│   ├── routes/            # HTTP REST endpoints (auth, traveller, ambulance, hospital, admin)
│   ├── services/          # Core workflows (allocation, reassignment, hospital dashboards)
│   ├── utils/             # Geolocation, unique Case IDs, slowapi rate limit, and logger
│   └── websocket/         # WebSocket managers and live event handlers
├── ml_models/             # Pickled RandomForest models (.pkl)
├── main.py                # FastAPI entrypoint
├── generate_dummy_model.py# Utility to train and serialize mock RandomForest classifiers
├── requirements.txt       # Python package requirements
├── .env.example           # Environment template
└── README.md              # Setup instructions
```

---

## 📋 Environment Configuration

Copy the `.env.example` file and create a `.env` in the root of the `backend/` folder:

```bash
# Firebase
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=smartrescue-ai

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# ML Model
ML_MODEL_PATH=./ml_models/smartrescue_final_model.pkl
CONFIDENCE_AUTO_TRIGGER=0.85
CONFIDENCE_ASK_THRESHOLD=0.50
FALSE_ALARM_BUFFER_SIZE=3

# Radius Boundaries
MAX_AMBULANCE_RADIUS_KM=50.0
MAX_HOSPITAL_RADIUS_KM=100.0

# Rate Limiting
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_SENSOR=120/minute

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## 📦 Installation & Setup

1. **Clone/Navigate to the backend directory:**
    ```bash
    cd IITM_RoadSafety/backend
    ```

2. **Create and Activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On Mac/Linux:
    source venv/bin/activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Generate the RandomForest model pickled file:**
    ```bash
    python generate_dummy_model.py
    ```

5. **Start the FastAPI server:**
    ```bash
    python main.py
    ```
    The Swagger API documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 WebSocket Channels

WebSockets can be connected using the following endpoints:

1.  **Ambulance Live Channel:** `/ws/ambulance/{ambulance_id}/{client_id}`
    *   Used by the ambulance app to stream live location updates.
2.  **Live Case Tracking Channel:** `/ws/tracking/{case_id}/{client_id}`
    *   Subscribed to by the Traveller and Hospital to track the ambulance en-route.
3.  **General Case Updates Feed:** `/ws/emergency/{case_id}/{client_id}`
    *   Fires realtime updates on case status lifecycle changes.
4.  **Hospital Emergency Dashboard:** `/ws/hospital/{hospital_id}/{client_id}`
    *   Feeds incoming ambulances, paramedic vital readings, and ETA clocks to trauma ward screens.
5.  **User Personal Alerts:** `/ws/user/{user_id}`
    *   Alerts traveller of pending confirmations or successful dispatches.

---

## 🧪 Sample Payload: stream sensor data

`POST /traveller/send-sensor-data`

```json
{
  "accelerometer_x": 32.4,
  "accelerometer_y": -12.8,
  "accelerometer_z": 15.6,
  "gyroscope_x": 4.1,
  "gyroscope_y": -3.2,
  "gyroscope_z": 2.8,
  "speed": 78.5,
  "heart_rate": 115.0,
  "orientation_x": 0.45,
  "orientation_y": -0.25,
  "orientation_z": 0.12,
  "latitude": 13.0827,
  "longitude": 80.2707
}
```
