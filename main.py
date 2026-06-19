import cv2
import os
import sys
import mss
import numpy as np
import pydirectinput
import keyboard
import time
import threading
import customtkinter as ctk # 🪄 Dàn áo Premium xịn xò

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

# ==========================================
# 🧠 LOGIC XỬ LÝ (Giữ nguyên 100% của đại gia)
# ==========================================

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối tới file, xài được cho cả lúc code và lúc build ra .exe """
    try:
        # PyInstaller tạo ra một thư mục tạm trong sys._MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def clear_keys():
    pydirectinput.keyUp("q")
    pydirectinput.keyUp("e")

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
    # Báo trạng thái lúc vừa sập UI
    lbl_status.config(text="Câu xong🎉🎉🎉! Đang cất cá vô túi...", fg="orange") 
    
    return wait_seconds(
        RECOVERY_DELAY_SEC,
        # Đếm ngược mượt mà, từ ngữ tự nhiên, báo rõ Bot chuẩn bị làm gì
        lambda remaining: f"Câu xong🎉🎉🎉! Tự động quăng lại sau {remaining}s...", 
    )

def fight_minigame(sct):
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
                lambda remaining: f"Đang chờ cá cắn câu, còn {remaining}s",
            ):
                break

            lbl_status.config(text="ĐANG BẮT ĐẦU CÂU CÁ...", fg="green")

            if not fight_minigame(sct):
                break

            lbl_status.config(text=f"Sắp quăng lại ô {rod_slot}...", fg="blue")


# ==========================================
# 🖥️ GIAO DIỆN PREMIUM MODERN (CUSTOMTKINTER)
# ==========================================
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue") 

class StatusLabelAdapter:
    """Thread-safe xịn xò đã được độ lại để tương thích CustomTkinter"""
    def __init__(self, widget):
        self._widget = widget

    def config(self, **kwargs):
        # Bộ lọc màu tự động dịch màu cơ bản sang mã Hex sang trọng
        color_map = {
            "red": "#ED4245",     # Đỏ Discord
            "blue": "#00B4D8",    # Xanh Ngọc
            "green": "#3BA55C",   # Xanh Lá Discord
            "orange": "#FEE75C",  # Vàng Neon nhẹ
            "black": "#A1A1AA"    # Xám khói
        }
        
        # Chuyển đổi 'fg' của tk thuần thành 'text_color' của ctk
        if 'fg' in kwargs:
            kwargs['text_color'] = color_map.get(kwargs.pop('fg'), "#E4E4E7")
            
        def _apply():
            self._widget.configure(**kwargs)

        self._widget.after(0, _apply)


def start_bot():
    global bot_running, bot_paused, rod_slot
    if not bot_running:
        bot_running = True
        bot_paused = False
        rod_slot = combo_slot.get()

        btn_start.configure(state="disabled", fg_color="#383A40")
        btn_pause.configure(state="normal", text="TẠM DỪNG (F6)", fg_color="#4F545C", hover_color="#686D73", text_color="#FFFFFF")
        btn_stop.configure(state="normal")
        combo_slot.configure(state="disabled")

        t = threading.Thread(target=auto_fishing_loop)
        t.daemon = True
        t.start()


def toggle_pause():
    global bot_paused, bot_running
    if bot_running:
        bot_paused = not bot_paused
        if bot_paused:
            clear_keys()
            btn_pause.configure(text="TIẾP TỤC (F6)", fg_color="#FEE75C", hover_color="#D4C14A", text_color="#18181B")
            lbl_status.config(text="Đã TẠM DỪNG. Lượn phố thôi!", fg="orange")
        else:
            btn_pause.configure(text="TẠM DỪNG (F6)", fg_color="#4F545C", hover_color="#686D73", text_color="#FFFFFF")
            lbl_status.config(text="Tiếp tục quăng cần! Cày tiền thôi!", fg="green")


def stop_bot():
    global bot_running, bot_paused
    bot_running = False
    bot_paused = False
    clear_keys()

    btn_start.configure(state="normal", fg_color="#5865F2")
    btn_pause.configure(state="disabled", text="TẠM DỪNG (F6)", fg_color="#383A40")
    btn_stop.configure(state="disabled")
    combo_slot.configure(state="readonly")
    lbl_status.config(text="Đã tắt Bot hoàn toàn.", fg="red")


keyboard.add_hotkey("f6", toggle_pause)

# Khởi tạo App với UI xịn
root = ctk.CTk()
root.title("CC anh Phúc lập trình ziên")
root.iconbitmap(resource_path("logo.ico"))
root.geometry("360x250")
root.attributes("-topmost", True)
root.configure(fg_color="#18181B") # Nền xám đen nhám

# Tiêu đề
lbl_title = ctk.CTkLabel(root, text="CHỌN Ô CẦN CÂU (1-5)", font=("Segoe UI", 13, "bold"), text_color="#E4E4E7")
lbl_title.pack(pady=(20, 10))

# Dropdown bo góc
combo_slot = ctk.CTkComboBox(root, values=["1", "2", "3", "4", "5"], width=130, height=32,
                             fg_color="#2B2D31", border_color="#383A40", 
                             button_color="#383A40", button_hover_color="#4F545C",
                             dropdown_fg_color="#2B2D31", dropdown_text_color="#E4E4E7",
                             text_color="#E4E4E7", font=("Segoe UI", 14, "bold"), state="readonly")
combo_slot.set("1")
combo_slot.pack(pady=(0, 20))

# Khung chứa nút
frame_btn = ctk.CTkFrame(root, fg_color="transparent")
frame_btn.pack(pady=5)

# 3 Nút bấm phẳng, không viền, màu xịn
btn_start = ctk.CTkButton(frame_btn, text="▶ BẬT BOT", width=80, height=35, corner_radius=6,
                          fg_color="#5865F2", hover_color="#4752C4", # Xanh Blurple Discord
                          font=("Segoe UI", 12, "bold"), command=start_bot)
btn_start.grid(row=0, column=0, padx=8)

btn_pause = ctk.CTkButton(frame_btn, text="⏸TẠM DỪNG (F6)", width=110, height=35, corner_radius=6,
                          fg_color="#383A40", hover_color="#4F545C", 
                          font=("Segoe UI", 12, "bold"), command=toggle_pause, state="disabled")
btn_pause.grid(row=0, column=1, padx=8)

btn_stop = ctk.CTkButton(frame_btn, text="❌TẮT", width=60, height=35, corner_radius=6,
                         fg_color="#ED4245", hover_color="#C9383A", # Đỏ
                         font=("Segoe UI", 12, "bold"), command=stop_bot, state="disabled")
btn_stop.grid(row=0, column=2, padx=8)

# Trả lại câu Slogan huyền thoại
_status_widget = ctk.CTkLabel(root, text="Bắt đầu treo thoiiii", font=("Segoe UI", 13, "italic"), text_color="#A1A1AA")
_status_widget.pack(pady=(15, 0))
lbl_status = StatusLabelAdapter(_status_widget)

root.mainloop()