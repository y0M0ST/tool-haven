import cv2
import mss
import numpy as np

# 🌟 ĐÃ XÍCH SANG PHẢI (Tăng left từ 550 lên 590)
prompt_monitor = {"top": 920, "left": 670, "width": 37, "height": 36}

print("🚀 ĐANG BẬT KÍNH HIỂN VI... (Bấm phím Q trên cửa sổ Camera để tắt)")

with mss.mss() as sct:
    while True:
        scr = np.array(sct.grab(prompt_monitor))
        img = cv2.cvtColor(scr, cv2.COLOR_BGRA2BGR)
        
        # Phóng to ảnh x2 lên cho đại gia dễ soi
        img_large = cv2.resize(img, (0, 0), fx=2.0, fy=2.0)
        
        cv2.imshow("KINH HIEN VI SOI NUT BEM TRAI", img_large)
        
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()