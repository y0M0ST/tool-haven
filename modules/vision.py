import os
import sys
import time

import cv2
import numpy as np

import modules.config as config
import modules.state as state

# 🌟 KHO DỮ LIỆU TEMPLATE (Load sẵn vào RAM để quét tốc độ ánh sáng)
TEMPLATES = {}


def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối tới file, xài được cho cả lúc code và lúc build ra .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_templates():
    global TEMPLATES
    # Map tên file ảnh với cặp phím chuẩn của pydirectinput
    template_files = {
        "q": ("q", "e"),
        "a": ("a", "d"),
        "z": ("z", "c"),
        "arr": ("left", "right") # Mũi tên trái/phải
    }
    for name, keys in template_files.items():
        path = resource_path(os.path.join("assets", f"tpl_{name}.png"))
        if os.path.exists(path):
            TEMPLATES[keys] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        else:
            print(f"[Cảnh báo] Khum tìm thấy file mẫu: {path}")


def identify_key_pair(sct):
    """ Mắt thần phụ (Bản Xuất Xưởng VIP PRO): Im lặng, nhanh như chớp, chính xác 99.9% """
    threshold = 0.75 # Ngưỡng sành điệu

    for _ in range(10):
        scr = np.array(sct.grab(config.prompt_monitor))
        gray = cv2.cvtColor(scr, cv2.COLOR_BGRA2GRAY)

        best_match = None
        max_val = 0

        for keys, tpl in TEMPLATES.items():
            if tpl is None: continue
            res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)
            if val > max_val:
                max_val = val
                if val > threshold:
                    best_match = keys

        if best_match:
            # Hiện lên UI cực sang
            show_l = "←" if best_match[0] == "left" else best_match[0].upper()
            show_r = "→" if best_match[1] == "right" else best_match[1].upper()
            state.lbl_status.configure(text=f"🔥 Chốt cặp: [ {show_l} ] - [ {show_r} ]", text_color="#00B4D8")
            return best_match # Rút êm!

        time.sleep(0.02)

    state.lbl_status.configure(text="⚠️ Khum soi ra đề, gồng đỡ Q-E!", text_color="#ED4245")
    return ("q", "e")


def scan_fish_bar(sct):
    screenshot = np.array(sct.grab(config.monitor))
    frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    fish_mask = cv2.inRange(hsv, config.fish_lower, config.fish_upper)
    bar_mask = cv2.inRange(hsv, config.bar_lower, config.bar_upper)
    bar_mask[0:50, :] = 0
    bar_mask[150:180, :] = 0

    return get_center_x(fish_mask), get_center_x(bar_mask)


def get_center_x(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 50:
            M = cv2.moments(c)
            if M["m00"] != 0:
                return int(M["m10"] / M["m00"])
    return None
