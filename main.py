import cv2
import mss
import numpy as np
import pydirectinput # 🪄 VŨ KHÍ MỚI: Giả lập phím bấm vật lý siêu cấp
import keyboard # Vẫn giữ lại để làm Hotkey F6 cho mượt
import time
import threading
import tkinter as tk
from tkinter import ttk

# Tắt tính năng tự động delay của pydirectinput (để Bot vẩy phím nhanh như chớp)
pydirectinput.PAUSE = 0.0

# ==========================================
# ⚙️ CẤU HÌNH THÔNG SỐ CỐT LÕI
# ==========================================
monitor = {"top": 850, "left": 660, "width": 600, "height": 180}
fish_lower = np.array([96, 160, 147])
fish_upper = np.array([176, 255, 255])
bar_lower = np.array([34, 62, 172])
bar_upper = np.array([131, 255, 255])

SLOT_KEYS = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}

FOCUS_COUNTDOWN_SEC = 3
WAIT_AFTER_CAST_SEC = 15
MISSING_UI_FRAMES = 25
UI_STABLE_FRAMES = 5
RECOVERY_DELAY_SEC = 1
FIGHT_DEADZONE = 15
ROD_KEY_HOLD_SEC = 0.3
FIGHT_LOOP_SLEEP = 0.02
SCAN_IDLE_SLEEP = 0.05

bot_running = False
bot_paused = False  
rod_slot = "1"

# Hàm dọn dẹp phím ảo đề phòng kẹt
def clear_keys():
    pydirectinput.keyUp('q')
    pydirectinput.keyUp('e')

def press_rod_slot():
    clear_keys()
    key = SLOT_KEYS.get(str(rod_slot), str(rod_slot))
    pydirectinput.keyDown(key)
    time.sleep(ROD_KEY_HOLD_SEC)
    pydirectinput.keyUp(key)

def wait_seconds(seconds, status_fn=None):
    ticks = int(seconds * 10)
    for tick in range(ticks):
        while bot_paused and bot_running:
            time.sleep(0.1)
        if not bot_running:
            return False
        if status_fn:
            remaining = max(1, int(seconds - tick * 0.1))
            lbl_status.config(text=status_fn(remaining), fg="green")
        time.sleep(0.1)
    return bot_running

def scan_fish_bar(sct):
    screenshot = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    fish_mask = cv2.inRange(hsv, fish_lower, fish_upper)
    bar_mask = cv2.inRange(hsv, bar_lower, bar_upper)
    bar_mask[0:50, :] = 0
    bar_mask[150:180, :] = 0

    return get_center_x(fish_mask), get_center_x(bar_mask)

def control_fish(diff, current_pressed):
    if diff > FIGHT_DEADZONE:
        if current_pressed != "e":
            pydirectinput.keyUp("q")
            pydirectinput.keyDown("e")
            return "e"
    elif diff < -FIGHT_DEADZONE:
        if current_pressed != "q":
            pydirectinput.keyUp("e")
            pydirectinput.keyDown("q")
            return "q"
    elif current_pressed is not None:
        clear_keys()
        return None
    return current_pressed

def finish_fight_and_recast():
    clear_keys()
    lbl_status.config(text="Câu xong! Chờ game cất cá...", fg="orange")
    return wait_seconds(
        RECOVERY_DELAY_SEC,
        lambda remaining: f"Câu xong! Chờ cất cá... còn {remaining}s",
    )

def fight_minigame(sct):
    """Mắt thần: Q/E khi thấy cá + thanh. Trả True khi UI biến mất -> cần quăng lại."""
    ui_seen = False
    missing_frames = 0
    ui_return_streak = 0
    current_pressed = None

    while bot_running:
        if bot_paused:
            if current_pressed is not None:
                clear_keys()
                current_pressed = None
            time.sleep(0.1)
            continue

        fish_x, bar_x = scan_fish_bar(sct)

        if fish_x is not None and bar_x is not None:
            ui_seen = True

            if missing_frames > 0:
                ui_return_streak += 1
                if ui_return_streak < UI_STABLE_FRAMES:
                    missing_frames += 1
                    if missing_frames > MISSING_UI_FRAMES:
                        return finish_fight_and_recast()
                    time.sleep(FIGHT_LOOP_SLEEP)
                    continue

            missing_frames = 0
            ui_return_streak = 0
            current_pressed = control_fish(fish_x - bar_x, current_pressed)
            time.sleep(FIGHT_LOOP_SLEEP)
            continue

        ui_return_streak = 0

        if current_pressed is not None:
            clear_keys()
            current_pressed = None

        if ui_seen:
            missing_frames += 1
            if missing_frames > MISSING_UI_FRAMES:
                return finish_fight_and_recast()
        else:
            time.sleep(SCAN_IDLE_SLEEP)

    clear_keys()
    return False

def get_center_x(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 50:
            M = cv2.moments(c)
            if M["m00"] != 0:
                return int(M["m10"] / M["m00"])
    return None

# ==========================================
# 🧠 LUỒNG CHẠY NGẦM (State machine)
# CAST -> WAIT 15s -> FIGHT -> RECAST (lặp)
# ==========================================
def auto_fishing_loop():
    global bot_running, bot_paused, rod_slot

    for i in range(FOCUS_COUNTDOWN_SEC, 0, -1):
        if not bot_running:
            return
        lbl_status.config(text=f"Mở game lẹ! Bot chạy sau {i}s...", fg="red")
        time.sleep(1)

    with mss.mss() as sct:
        while bot_running:
            lbl_status.config(text=f"Quăng cần ô số {rod_slot}!", fg="blue")
            press_rod_slot()

            if not wait_seconds(
                WAIT_AFTER_CAST_SEC,
                lambda remaining: f"Chờ nhân vật câu cá... còn {remaining}s",
            ):
                break

            lbl_status.config(text="Mắt thần ON! Canh cá + thanh mục tiêu...", fg="green")

            if not fight_minigame(sct):
                break

            lbl_status.config(text=f"Sắp quăng lại ô {rod_slot}...", fg="blue")

# ==========================================
# 🖥️ GIAO DIỆN APP TKINTER 
# ==========================================
def start_bot():
    global bot_running, bot_paused, rod_slot
    if not bot_running:
        bot_running = True
        bot_paused = False
        rod_slot = combo_slot.get()
        
        btn_start.config(state=tk.DISABLED)
        btn_pause.config(state=tk.NORMAL, text="TẠM DỪNG (F6)", bg="#fca311")
        btn_stop.config(state=tk.NORMAL)
        combo_slot.config(state=tk.DISABLED)
        
        t = threading.Thread(target=auto_fishing_loop)
        t.daemon = True
        t.start()

def toggle_pause():
    global bot_paused, bot_running
    if bot_running:
        bot_paused = not bot_paused
        if bot_paused:
            clear_keys()
            btn_pause.config(text="TIẾP TỤC (F6)", bg="#a4de02")
            lbl_status.config(text="Đã TẠM DỪNG", fg="#d35400")
        else:
            btn_pause.config(text="TẠM DỪNG (F6)", bg="#fca311")
            lbl_status.config(text="Tiếp tục quăng cần! Cày tiền thôi!", fg="green")

def stop_bot():
    global bot_running, bot_paused
    bot_running = False
    bot_paused = False
    clear_keys()
    
    btn_start.config(state=tk.NORMAL)
    btn_pause.config(state=tk.DISABLED, text="TẠM DỪNG (F6)", bg="#e0e0e0")
    btn_stop.config(state=tk.DISABLED)
    combo_slot.config(state="readonly")
    lbl_status.config(text="Đã tắt Bot hoàn toàn.", fg="red")

keyboard.add_hotkey('f6', toggle_pause)

root = tk.Tk()
root.title("Cc anh Phúc lập trình ziên")
root.geometry("320x220")
root.attributes('-topmost', True)

tk.Label(root, text="CHỌN Ô CẦN CÂU (1-5):", font=("Arial", 10, "bold")).pack(pady=10)

combo_slot = ttk.Combobox(root, values=["1", "2", "3", "4", "5"], state="readonly", width=10)
combo_slot.current(0)
combo_slot.pack()

frame_btn = tk.Frame(root)
frame_btn.pack(pady=15)

btn_start = tk.Button(frame_btn, text="BẬT BOT", bg="#a4de02", font=("Arial", 9, "bold"), width=8, command=start_bot)
btn_start.grid(row=0, column=0, padx=4)

btn_pause = tk.Button(frame_btn, text="TẠM DỪNG (F6)", bg="#e0e0e0", font=("Arial", 9, "bold"), width=14, command=toggle_pause, state=tk.DISABLED)
btn_pause.grid(row=0, column=1, padx=4)

btn_stop = tk.Button(frame_btn, text="TẮT", bg="#ff4040", fg="white", font=("Arial", 9, "bold"), width=6, command=stop_bot, state=tk.DISABLED)
btn_stop.grid(row=0, column=2, padx=4)

lbl_status = tk.Label(root, text="Bắt đầu treo thoiiii", fg="black", font=("Arial", 9, "italic"))
lbl_status.pack()

root.mainloop() 