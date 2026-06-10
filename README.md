# 🤖 Glass Defect Classification & Automated Sorting System

An end-to-end industrial automation pipeline combining **Computer Vision (YOLOv8)**, **Industrial Cameras (Hikrobot)**, and **Robotic Arms (Dobot Magician)** to inspect, classify, and sort glass products based on structural integrity.

---

## 🌟 Key Features

*   **Industrial Camera Integration:** Direct low-latency frame grabbing utilizing the Hikrobot MVS SDK via `ctypes`.
*   **Real-time AI Inspection:** Object detection powered by custom-trained YOLOv8 to classify glass status (`Normal`, `NonBroken`, `Broken`).
*   **Intelligent Delay Buffer:** Implements a time-window validation logic (`DECISION_TIME`) to prevent false triggers from momentary noise.
*   **Thread/Stream-Safe Robot Execution:** Automatically pauses camera grabbing and flushes buffers during robotic actions to prevent frame lag and buffer overflow.
*   **Dual-Mode CLI:** Includes a live production automation mode and a utility mode for real-time robotic coordinate calibration.

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

## 📋 Prerequisites & Project Structure

### 1. Hardware Dependencies

* **Robotic Arm:** Dobot Magician (Connected via USB, e.g., `COM4`).
* **Camera:** Hikrobot Industrial Camera (GigE or USB) with **MVS (Machine Vision Suite)** installed.

### 2. Project Directory Setup

Before running the project, ensure your workspace is structured as follows:

```text
├── MvImport/              # Copy this folder from your Hikrobot MVS Installation SDK
│   ├── MvCameraControl_class.py
│   └── ...
├── best.pt                # Your custom-trained YOLOv8 weights file
├── main.py                # The main application script
└── requirements.txt       # Python library dependencies

```

> ⚠️ **Important Note on Hikrobot SDK:** The script automatically attempts to locate the `MvCameraControl.dll` dynamic link library from the official MVS default installation paths (`C:\Program Files\Common Files\MVS\...`). Ensure MVS is fully installed on your Windows machine.

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

## 🎮 How to Use

Run the main application script:

```bash
python main.py

```

You will be prompted with a dual-mode interactive menu:

```text
=======================================
      GLASS DETECTION ROBOT SYSTEM     
=======================================
[1] Run Automated System
[2] Calibration Mode (Read Robot Coordinates)
=======================================
👉 Select Mode (1 or 2): 

```

### Mode 1: Automated Production System

* Activates the camera feed and AI pipeline.
* Keeps track of detected glass objects. If an object remains stable for `3.0 seconds` (configurable), the robot arm engages to sort it to its respective bin (Broken vs. Non-Broken).
* Press **`q`** on the camera window display to gracefully shut down the system.

### Mode 2: Calibration Tool

* A utility helper that tracks and streams live `X, Y, Z, R` spatial coordinates of the Dobot arm to the terminal.
* Use this mode to manually position the arm to your pick/drop locations and copy the coordinates into the script variables (`PICK_DOWN`, `DROP_LEFT_HOVER`, etc.).

---

## ⚙️ Configuration & Customization

You can fine-tune system behaviors directly inside `main.py`:

```python
# Hardware Ports
DOBOT_PORT = 'COM4' 

# Time (seconds) the object must stay under the camera before picking
DECISION_TIME = 3.0 

# Confidence thresholds customized per class label
CONFIDENCE_THRESHOLDS = {
    "Broken": 0.25,    
    "Normal": 0.25,    
    "NonBroken": 0.25  
}

```

---

## 🛡️ Exception Handling & Safety

* **Robust De-initialization:** The script wraps vital communication bindings inside `try...finally` structures. If an unhandled crash or a keyboard interruption (`Ctrl+C`) happens, it forces the vacuum suction cup off and closes all serial/camera communication pipelines safely.
* **Thread Buffer Guard:** Halting camera grabbing during robotic movement prevents memory inflation and old-frame queuing, keeping your real-time processing strictly synchronized.