import os
import sys
import time
import cv2
import numpy as np
from ctypes import *
from ultralytics import YOLO

# ==============================================================================
# --- 1. ส่วนแก้ปัญหา FileNotFoundError: MvCameraControl.dll ---
# ==============================================================================
mvs_possible_paths = [
    r"C:\Program Files\Common Files\MVS\Runtime\Win64_x64",
    r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64"
]
if os.environ.get('MVCAM_COMMON_RUNENV'):
    mvs_possible_paths.insert(0, os.environ.get('MVCAM_COMMON_RUNENV'))

for path in mvs_possible_paths:
    if os.path.exists(path):
        os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
        if sys.version_info >= (3, 8) and sys.platform.startswith('win'):
            try:
                os.add_dll_directory(path)
            except Exception:
                pass

# ==============================================================================
# --- 2. นำเข้าไลบรารีของ Hikrobot และ Dobot ---
# ==============================================================================
try:
    from MvImport.MvCameraControl_class import *
except ImportError:
    print("❌ ไม่พบโฟลเดอร์ MvImport (สำหรับ Hikrobot) โปรดตรวจสอบโครงสร้างโฟลเดอร์")
    sys.exit()

try:
    from pydobot import Dobot
except ImportError:
    print("❌ โปรดติดตั้ง pydobot ก่อน โดยพิมพ์: pip install pydobot pyserial")
    sys.exit()

# ==============================================================================
# 🎯 3. [ตั้งค่าระบบ AI และ แขนกลที่นี่] 
# ==============================================================================
DOBOT_PORT = 'COM4' 

DECISION_TIME = 3.0 # ⏱️ เวลาตัดสินใจยืนยันผล (วินาที)

# 🧠 ตั้งค่าความมั่นใจ (ต้องสัมพันธ์กับค่า conf ในลูปด้านล่าง)
CONFIDENCE_THRESHOLDS = {
    "Broken": 0.25,    
    "Normal": 0.25,    
    "NonBroken": 0.25  
}
DEFAULT_CONF = 0.50 

HOME_POS         = (150,    0, 100, 0)
PICK_HOVER       = (163,    66.69,  -9.77, 0)
PICK_DOWN        = (167.97,    66.68, -55.57, 0)
DROP_LEFT_HOVER  = (219.46,  -56.24,  27.93, 0)
DROP_LEFT_DOWN   = (223.73,  -52.29, -23.84, 0)
DROP_RIGHT_HOVER = (106.46, 204.26,  36.22, 0)
DROP_RIGHT_DOWN  = (118.55, 222.66, -21.05, 0)
# ==============================================================================

def mode_read_coordinates():
    print(f"\nกำลังเชื่อมต่อ Dobot ที่พอร์ต {DOBOT_PORT}...")
    device = None
    try:
        device = Dobot(port=DOBOT_PORT, verbose=False)
        print("\n✅ เชื่อมต่อสำเร็จ! กด Ctrl+C เพื่อออก")
        while True:
            pose = device.pose()
            print(f"\r📍 พิกัด ->  X:{pose[0]:6.2f} | Y:{pose[1]:6.2f} | Z:{pose[2]:6.2f} | R:{pose[3]:6.2f}   ", end="")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n👋 ปิดโหมดตั้งค่า")
    except Exception as e:
        print(f"\n❌ ข้อผิดพลาด: {e}")
    finally:
        if device:
            device.close()

def move_glass(device, glass_type):
    print(f"\n🤖 สั่งงาน: กำลังจัดการกระจกประเภท [{glass_type}]")
    device.move_to(*PICK_HOVER, wait=True)
    device.move_to(*PICK_DOWN, wait=True)
    device.suck(True) 
    time.sleep(0.5)   
    device.move_to(*PICK_HOVER, wait=True)
    
    if glass_type == "Broken":
        device.move_to(*DROP_LEFT_HOVER, wait=True)
        device.move_to(*DROP_LEFT_DOWN, wait=True)
    else:
        device.move_to(*DROP_RIGHT_HOVER, wait=True)
        device.move_to(*DROP_RIGHT_DOWN, wait=True)
        
    device.suck(False) 
    time.sleep(0.5)    
    
    if glass_type == "Broken":
        device.move_to(*DROP_LEFT_HOVER, wait=True)
    else:
        device.move_to(*DROP_RIGHT_HOVER, wait=True)
        
    device.move_to(*HOME_POS, wait=True)
    print("✅ ทำงานเสร็จ กลับจุดพัก")

def mode_auto_system():
    dobot = None
    cam = None
    
    try:
        dobot = Dobot(port=DOBOT_PORT, verbose=False)
        dobot.move_to(*HOME_POS, wait=True)
        dobot.suck(False) 
        print("✅ เชื่อมต่อ Dobot สำเร็จ!")
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อ Dobot: {e}")
        return

    print("กำลังโหลดโมเดล YOLO...")
    try:
        model = YOLO('best.pt')
    except Exception as e:
        print(f"❌ ไม่พบไฟล์โมเดล 'best.pt': {e}")
        dobot.close()
        return

    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
    MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if deviceList.nDeviceNum == 0:
        print("❌ ไม่พบกล้อง Hikrobot")
        dobot.close()
        return

    cam = MvCamera()
    stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
    cam.MV_CC_CreateHandle(stDeviceList)
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print("❌ เปิดกล้องไม่ได้")
        dobot.close()
        return

    cam.MV_CC_StartGrabbing()
    stOutFrame = MV_FRAME_OUT()
    memset(byref(stOutFrame), 0, sizeof(stOutFrame))

    print("\n✅ ระบบพร้อมทำงาน! (กด 'q' ที่หน้าต่างภาพเพื่อออก)")
    
    is_robot_moving = False 
    detection_start_time = None
    target_class_name = None

    try:
        while True:
            ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            
            if ret == 0:
                pData = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()
                cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr, stOutFrame.stFrameInfo.nFrameLen)
                data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nFrameLen), dtype=np.uint8)
                
                if stOutFrame.stFrameInfo.enPixelType == 0x01180014: 
                    image = data.reshape((stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth, 3))
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                else:
                    image = data.reshape((stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth))
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                
                results = model(image, conf=0.20, iou=0.45, verbose=False)
                annotated_frame = results[0].plot()
                
                if not is_robot_moving:
                    valid_detection = False
                    class_name = ""
                    
                    if len(results[0].boxes) > 0:
                        best_box = results[0].boxes[0]
                        class_name = model.names[int(best_box.cls[0])]
                        confidence = float(best_box.conf[0])
                        
                        req_conf = CONFIDENCE_THRESHOLDS.get(class_name, DEFAULT_CONF)
                        
                        if confidence >= req_conf:
                            valid_detection = True
                        else:
                            print(f"\r⚠️ เจอ {class_name} แต่ความมั่นใจต่ำไป ({confidence:.2f} < {req_conf:.2f})", end="")

                    if valid_detection:
                        if detection_start_time is None:
                            detection_start_time = time.time()
                            target_class_name = class_name
                            print(f"\n⏳ พบ [{class_name}] ({confidence:.2f})! เริ่มนับถอยหลัง {DECISION_TIME} วินาที")
                        elif class_name == target_class_name:
                            elapsed = time.time() - detection_start_time
                            countdown = max(0, DECISION_TIME - elapsed)
                            
                            cv2.putText(annotated_frame, f"Wait: {countdown:.1f}s", (30, 60), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 165, 255), 4)
                            
                            if elapsed >= DECISION_TIME:
                                print(f"🎯 ยืนยันผลว่าเป็น [{class_name}]! สั่งแขนกลทำงาน")
                                is_robot_moving = True 
                                cv2.imshow("Hikrobot + Dobot System", cv2.resize(annotated_frame, (800, 600)))
                                cv2.waitKey(1)
                                
                                # 💡 [FIX] หยุดดึงภาพชั่วคราวและคืนบัฟเฟอร์ เพื่อป้องกันคิวภาพค้างระหว่างแขนกลขยับ
                                cam.MV_CC_FreeImageBuffer(stOutFrame)
                                cam.MV_CC_StopGrabbing()
                                
                                move_glass(dobot, class_name) 
                                
                                # เริ่มดึงภาพใหม่อีกครั้งหลังจากแขนกลทำงานเสร็จ
                                cam.MV_CC_StartGrabbing()
                                is_robot_moving = False 
                                detection_start_time = None 
                                continue # วนลูปใหม่ทันที ไม่จำเป็นต้องวิ่งไป FreeImageBuffer ด้านล่างซ้ำ
                        else:
                            detection_start_time = time.time()
                            target_class_name = class_name
                    else:
                        if detection_start_time is not None:
                            print("\n❌ วัตถุหายไป หรือไม่มั่นใจพอ ยกเลิกการตรวจสอบ")
                            detection_start_time = None
                
                cv2.imshow("Hikrobot + Dobot System", cv2.resize(annotated_frame, (800, 600)))
                cam.MV_CC_FreeImageBuffer(stOutFrame)
                
            else:
                print(f"⚠️ รอภาพจากกล้อง... (รหัส Error: {ret})")
                time.sleep(0.5)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except Exception as main_err:
        print(f"\n❌ เกิดข้อผิดพลาดระหว่างรันระบบ: {main_err}")
        
    finally:
        print("\nกำลังปิดระบบและคืนทรัพยากร...")
        if dobot:
            try:
                dobot.suck(False)
                dobot.close()
            except: pass
        if cam:
            try:
                cam.MV_CC_StopGrabbing()
                cam.MV_CC_CloseDevice()
                cam.MV_CC_DestroyHandle()
            except: pass
        cv2.destroyAllWindows()

if __name__ == '__main__':
    print("=======================================")
    print("      GLASS DETECTION ROBOT SYSTEM     ")
    print("=======================================")
    print("[1] รันระบบอัตโนมัติ")
    print("[2] โหมดตั้งค่า (อ่านพิกัดแขนกล)")
    print("=======================================")
    
    choice = input("👉 เลือกโหมด (1 หรือ 2): ")
    if choice == '1':
        mode_auto_system()
    elif choice == '2':
        mode_read_coordinates()
    else:
        print("❌ ตัวเลือกไม่ถูกต้อง")