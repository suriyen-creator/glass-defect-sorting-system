# 🤖 Glass Defect Classification & Automated Sorting System

An end-to-end industrial automation pipeline combining **Computer Vision (YOLOv8)**, **Industrial Cameras (Hikrobot)**, and **Robotic Arms (Dobot Magician)** to inspect, classify, and sort glass products based on structural integrity.

---

## 🌟 Key Features

* **Industrial Camera Integration:** Direct low-latency frame grabbing utilizing the Hikrobot MVS SDK via Windows `ctypes`.
* **Real-time AI Inspection:** Object detection powered by custom-trained YOLOv8 to classify glass status into 2 distinct classes (`Broken` and `NonBroken`).
* **Intelligent Delay Buffer:** Implements a time-window validation logic (`DECISION_TIME`) to prevent false triggers from temporary visual noise or motion.
* **Thread/Stream-Safe Robot Execution:** Pauses camera grabbing and flushes buffers during robotic actions to prevent frame lag and buffer overflow.
* **Dedicated Calibration Tool:** Includes a separate utility script (`get_pos.py`) to stream real-time coordinate changes for rapid physical setup.

---

## 🏗️ System Architecture

```text
 ┌─────────────────┐      ┌─────────────┐      ┌─────────────────┐
 │ Hikrobot Camera │ ───> │   YOLOv8    │ ───> │  Dobot Magician │
 │  (MVS SDK DLL)  │      │ (Inference) │      │  (Robotic Arm)  │
 └─────────────────┘      └─────────────┘      └─────────────────┘

```

1. **Capture:** The Hikrobot camera streams frames into an RGB/Grayscale NumPy array.
2. **Analyze:** YOLOv8 processes the frame; if a class confidence passes the strict threshold barrier, a countdown begins.
3. **Act:** Once confirmed, camera ingestion temporarily pauses while the Dobot executes the pick-and-place sequence based on the target class.

---

## 📋 Project Structure & Prerequisites

### 1. File Structure

Ensure your workspace directory looks like this before running the application:

```text
├── MvImport/              # Hikrobot MVS Installation SDK folder
│   ├── MvCameraControl_class.py
│   └── ...
├── best.pt                # Trained YOLOv8 weights (Download via GitHub Releases)
├── data.yaml              # Dataset configuration (2 classes: Broken, NonBroken)
├── main.py                # Main automated production system
├── get_pos.py             # Robotic arm coordinate calibration utility
└── requirements.txt       # Python dependencies

```

### 2. Hardware Dependencies

* **Robotic Arm:** Dobot Magician (Connected via USB, default port configured to `COM4`).
* **Camera:** Hikrobot Industrial Camera (GigE or USB) with **MVS (Machine Vision Suite)** installed.

> ⚠️ **Important SDK Note:** The code automatically looks for `MvCameraControl.dll` in Windows standard paths (`C:\Program Files\Common Files\MVS\...`). Make sure MVS is fully installed.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
```bash
git clone [https://github.com/yourusername/glass-sorting-system.git](https://github.com/yourusername/glass-sorting-system.git)
cd glass-sorting-system

```


2. **Install Python dependencies:**
```bash
pip install -r requirements.txt

```



---

## 🎮 How to Run

### 1. Calibration & Setup (First-time deployment)

Before running the sorting automation, you must map out your physical workspace coordinates:

```bash
python get_pos.py

```

* **Instructions:** Press and hold the black unlock button on the Dobot arm and manually move it to your picking point, home point, and drop bins.
* The terminal will print the live `X, Y, Z, R` coordinates. Copy these values and update the coordinate variables inside `main.py`.

### 2. Running the Sorting Automation

Once calibrated, initiate the main real-time automated sorting system:

```bash
python main.py

```

* Select **`[1] Run Automated System`** from the terminal prompt menu.
* The AI pipeline will start tracking objects. If a piece of glass is continuously detected as `Broken` or `NonBroken` for `3.0 seconds`, the robotic arm will automatically grab it and sort it into its designated zone.
* Press **`q`** while focusing on the video window to gracefully disconnect and shut down the system.

---

## ⚙️ Configuration Tuning

You can adjust parameters inside `main.py` to match your hardware setup:

```python
# Hardware Port Configuration
DOBOT_PORT = 'COM4' 

# Stabilization window delay (in seconds)
DECISION_TIME = 3.0 

# Confidence threshold filters
CONFIDENCE_THRESHOLDS = {
    "Broken": 0.25,    
    "NonBroken": 0.25  
}

```

---

## 🛡️ Exception Handling & Safety

* **Graceful Termination:** The script uses comprehensive `try...finally` blocks. If an unhandled error occurs or `Ctrl+C` is pressed, the system automatically turns off the vacuum suction cup and safely releases the camera handle and serial ports.
* **Buffer Lock Mitigation:** Halting camera tracking during robotic operations protects memory buffers from queuing up stale frames, ensuring that when the robot finishes a task, the next camera frame processed is completely real-time.