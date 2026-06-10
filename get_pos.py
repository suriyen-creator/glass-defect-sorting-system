from pydobot import Dobot
import time
import sys

# เปลี่ยนพอร์ต 'COM3' ให้ตรงกับที่ Dobot ของคุณใช้งานอยู่
DOBOT_PORT = 'COM4'

def main():
    print(f"กำลังเชื่อมต่อ Dobot ที่พอร์ต {DOBOT_PORT}...")
    try:
        # เชื่อมต่อกับ Dobot
        device = Dobot(port=DOBOT_PORT, verbose=False)
        print("\n✅ เชื่อมต่อสำเร็จ!")
        print("=====================================================")
        print("👉 วิธีใช้งาน:")
        print("1. กดปุ่มสีดำบนแขนกล (ปุ่มปลดล็อคมอเตอร์) ค้างไว้")
        print("2. ใช้มือจับแขนกลลากไปยังจุดต่างๆ (จุดหยิบ, จุดวาง)")
        print("3. จดตัวเลขพิกัด X, Y, Z บนหน้าจอนี้ ไปใส่ในโค้ดหลัก")
        print("🛑 กดปุ่ม Ctrl + C บนคีย์บอร์ด เมื่อต้องการหยุดการทำงาน")
        print("=====================================================\n")

        # วนลูปอ่านค่าพิกัดตลอดเวลา
        while True:
            # คำสั่ง device.pose() จะคืนค่ากลับมาเป็น (x, y, z, r, j1, j2, j3, j4)
            current_pose = device.pose()
            x, y, z, r = current_pose[0], current_pose[1], current_pose[2], current_pose[3]
            
            # ปริ้นท์ค่าออกมา (ใช้ \r เพื่อให้มันอัปเดตทับบรรทัดเดิม จะได้ไม่รกหน้าจอ)
            print(f"\r📍 พิกัดปัจจุบัน ->  X: {x:6.2f}  |  Y: {y:6.2f}  |  Z: {z:6.2f}  |  R: {r:6.2f}      ", end="")
            
            # อัปเดตค่าทุกๆ 0.2 วินาที
            time.sleep(0.2)

    except KeyboardInterrupt:
        # เมื่อกด Ctrl+C ให้ปิดการเชื่อมต่ออย่างปลอดภัย
        print("\n\n🛑 ยกเลิกการอ่านค่า... กำลังปิดการเชื่อมต่อ")
        device.close()
        sys.exit()
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        print("โปรดเช็คว่าพอร์ต COM ถูกต้อง และไม่ได้เปิดโปรแกรมอื่นที่กำลังใช้ Dobot อยู่")

if __name__ == '__main__':
    main()