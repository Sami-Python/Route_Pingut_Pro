# Startup Guide for Pingut Project

This guide explains how to start the necessary services for the project: the Open-Meteo backend (using Docker) and the main API Gateway.

## Prerequisites

- **Docker Desktop**: Ensure Docker Desktop is installed and running.
- **Python**: Ensure you have the project's Python environment activated.

## 1. Start Open-Meteo Services (Docker)

The weather data service runs in a Docker container. You only need to do this once per session.

### Option A: Using Docker Compose (Recommended)
Run this command from the project root (`~/code/pingut-projekti-4`):

```powershell
docker-compose -f open_meteo/docker-compose.yml up -d
```

- `-d` runs the containers in the background (detached mode).
- To view logs: `docker-compose -f open_meteo/docker-compose.yml logs -f`
- To stop: `docker-compose -f open_meteo/docker-compose.yml down`

---

## 2. Start the Main API

Once the Docker containers are running, start the main FastAPI backend in a new terminal.

```powershell
uvicorn api.main:app --reload --host 0.0.0.0
```

- The API will be available at: `http://localhost:8000`
- It connects to the Open-Meteo service at `http://localhost:8081`

## 3. Verify Connectivity

You can verify everything is working by opening:
- **Main API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Open-Meteo Health**: [http://localhost:8081](http://localhost:8081)

## Troubleshooting

- **WinError 10061**: Usually means the Docker container is not running. Run the docker-compose command from Step 1.
- **Port Conflicts**: If port 8081 is busy, ensure no other instance of the backend is running.
- **Merge Conflicts**: If you pull new code, run `git status` to check for conflicts before starting.

---

## 4. Mobile App Connectivity (IMPORTANT)

If you are running the mobile app on a physical Android device, follow these steps to ensure connectivity:

### A. Windows Firewall
The Windows Firewall often blocks incoming connections from the phone.
Run the provided script as **Administrator** to open ports 8000 (API) and 8081 (Weather):

1. Find `fix_firewall.ps1` in the project root.
2. Right-click -> "Run with PowerShell".

### B. PowerShell vs WSL
**CRITICAL:** Do NOT run the main API (`uvicorn`) inside WSL (Ubuntu/Linux terminal). The phone cannot see the WSL network easily.
**Always run `uvicorn` in a standard Windows PowerShell terminal:**

```powershell
# Correct (Windows PowerShell)
PS C:\Users\samih\code\pingut-projekti-4> .\.venv\Scripts\activate
PS C:\Users\samih\code\pingut-projekti-4> uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### C. Check Connection
Open your phone's browser and go to `http://<YOUR_PC_IP>:8000/docs`. If this doesn't load, the app will not work.
