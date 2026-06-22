import ctypes
import random
import time

import mss
import pydirectinput

import modules.config as config
import modules.state as state
from modules.vision import scan_fish_bar, identify_key_pair, find_alt_target_center, load_templates

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

pydirectinput.PAUSE = 0.0


def os_cef_click():
    """ Nhấp chuột OS đủ lâu để CEF WebView ox_target ghi nhận """
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(random.uniform(0.045, 0.065))
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def os_lightning_snap(dest_x, dest_y):
    """ Vẩy trỏ chuột sấm sét (Đã tối ưu cho màn hình 60Hz) """
    tx = int(dest_x + random.uniform(-1.5, 1.5))
    ty = int(dest_y + random.uniform(-1.5, 1.5))
    user32.SetCursorPos(tx, ty)
    time.sleep(random.uniform(0.018, 0.028))


def clear_keys():
    """ Kháng thể giải giáp mọi loại phím bị kẹt """
    for k in ["q", "e", "a", "d", "z", "c", "left", "right", "alt", "altleft", "altright"]:
        pydirectinput.keyUp(k)


def press_rod_slot():
    clear_keys()
    key = config.SLOT_KEYS.get(str(state.rod_slot), str(state.rod_slot))
    pydirectinput.keyDown(key)
    time.sleep(random.uniform(0.24, 0.38))
    pydirectinput.keyUp(key)

def wait_seconds(seconds, status_fn=None):
    ticks = int(seconds * 10)
    for tick in range(ticks):
        while state.bot_paused and state.bot_running:
            time.sleep(random.uniform(0.08, 0.12))
        if not state.bot_running:
            return False
        if status_fn:
            remaining = max(1, int(seconds - tick * 0.1))
            state.lbl_status.config(text=status_fn(remaining), fg="green")
        time.sleep(random.uniform(0.08, 0.12))
    return state.bot_running

def control_fish(diff, current_pressed):
    if random.random() < 0.015:
        clear_keys() 
        wrong_key = state.active_key_left if diff > 0 else state.active_key_right
        pydirectinput.keyDown(wrong_key)
        time.sleep(random.uniform(0.04, 0.08)) 
        pydirectinput.keyUp(wrong_key)
        time.sleep(random.uniform(0.12, 0.18))
        return None 

    if diff > config.FIGHT_DEADZONE: 
        if current_pressed != state.active_key_right:
            if current_pressed: pydirectinput.keyUp(current_pressed)
            pydirectinput.keyDown(state.active_key_right)
            return state.active_key_right

    elif diff < -config.FIGHT_DEADZONE: 
        if current_pressed != state.active_key_left:
            if current_pressed: pydirectinput.keyUp(current_pressed)
            pydirectinput.keyDown(state.active_key_left)
            return state.active_key_left

    elif current_pressed is not None:
        clear_keys()
        return None
        
    return current_pressed

def finish_fight_and_recast():
    clear_keys()
    state.lbl_status.config(text="Câu xong🎉! Đang cất cá vô túi...", fg="orange")
    recovery_sec = config.RECOVERY_DELAY_SEC + random.uniform(0.1, 0.5)
    return wait_seconds(
        recovery_sec,
        lambda remaining: f"Câu xong🎉! Tự động quăng lại sau {remaining}s...",
    )

def fight_minigame(sct):
    ui_seen = False
    missing_frames = 0
    ui_return_streak = 0
    current_pressed = None
    exam_read = False 

    while state.bot_running:
        if state.bot_paused:
            if current_pressed is not None:
                clear_keys()
                current_pressed = None
            time.sleep(0.1)
            continue

        fish_x, bar_x = scan_fish_bar(sct)

        if fish_x is not None and bar_x is not None:
            ui_seen = True

            if not exam_read:
                state.active_key_left, state.active_key_right = identify_key_pair(sct)
                show_l = "←" if state.active_key_left == "left" else state.active_key_left.upper()
                show_r = "→" if state.active_key_right == "right" else state.active_key_right.upper()
                state.lbl_status.config(text=f"Chốt cặp phím: [ {show_l} ] - [ {show_r} ]", fg="blue")
                exam_read = True

            if missing_frames > 0:
                ui_return_streak += 1
                if ui_return_streak < config.UI_STABLE_FRAMES:
                    missing_frames += 1
                    if missing_frames > config.MISSING_UI_FRAMES:
                        return finish_fight_and_recast()
                    time.sleep(random.uniform(0.016, 0.032))
                    continue

            missing_frames = 0
            ui_return_streak = 0
            current_pressed = control_fish(fish_x - bar_x, current_pressed)
            time.sleep(random.uniform(0.016, 0.032))
            continue

        ui_return_streak = 0

        if current_pressed is not None:
            clear_keys()
            current_pressed = None

        if ui_seen:
            missing_frames += 1
            if missing_frames > config.MISSING_UI_FRAMES:
                return finish_fight_and_recast()
        else:
            time.sleep(random.uniform(0.04, 0.07))

    clear_keys()
    return False

# ====================================================================
# 🚀 ĐỘNG CƠ ALT-TARGET — Pacifist Turbo Protocol (ĐÃ FIX 2 BOM ẨN)
# ====================================================================
def execute_alt_step(sct, template_name, step_title, menu_click_pos=None):
    alt_key = "altleft"
    pydirectinput.keyDown(alt_key)
    time.sleep(random.uniform(0.20, 0.28))

    for _ in range(15):
        if not state.bot_running:
            pydirectinput.keyUp(alt_key)
            return False

        # 🧠 FIX BOM SỐ 2: BẮT PAUSE (F6) TỨC THỜI NGAY TRONG VÒNG LẶP!
        if state.bot_paused:
            pydirectinput.keyUp(alt_key) # Giải phóng phím Alt ngay để user xài máy!
            while state.bot_paused and state.bot_running:
                time.sleep(0.1)
            if not state.bot_running: return False
            # Vừa được thả Pause -> Gồng Alt lại từ đầu và chờ mắt bung
            pydirectinput.keyDown(alt_key)
            time.sleep(random.uniform(0.20, 0.28))
            continue # Reset lại lượt quét

        pydirectinput.keyDown(alt_key)

        coords = find_alt_target_center(sct, template_name)
        if coords is not None:
            x, y = coords

            state.lbl_status.config(text=f"Click 1 — Icon ({x}, {y})", fg="blue")
            os_lightning_snap(x, y)
            time.sleep(random.uniform(0.025, 0.040))
            os_cef_click()

            time.sleep(random.uniform(0.22, 0.28))

            if menu_click_pos is not None:
                pydirectinput.keyDown(alt_key)
                mx, my = menu_click_pos
                state.lbl_status.config(text=f"Click 2 — Menu ({mx}, {my})", fg="blue")
                os_lightning_snap(mx, my)
                time.sleep(random.uniform(0.030, 0.050))
                os_cef_click()
                
            # ==========================================================
            # 🛡️ KÍNH CHIẾU YÊU (BẮT BUỘC PHẢI CÓ ĐỂ CHỐNG BÁO CÁO LÁO)
            # ==========================================================
            pydirectinput.keyDown(alt_key)
            time.sleep(random.uniform(0.45, 0.55)) 
            
            re_check = find_alt_target_center(sct, template_name)
            
            if re_check is not None:
                # ❌ Kêu xịt! Icon vẫn còn lù lù nè!
                state.lbl_status.config(text="⏳ Lag chưa ăn! Đứng thở 0.5s ròii gõ bồi...", fg="orange")
                # 🧠 FIX BOM SỐ 1: GỒNG ALT TRƯỚC KHI ĐI NGỦ 0.5s CHỐNG SẬP UI!
                pydirectinput.keyDown(alt_key) 
                time.sleep(0.5)
                continue 
            else:
                # ✅ Icon nổ tung thật sự -> Mới được phép nhả Alt và báo cáo hoàn thành!
                pydirectinput.keyUp(alt_key)
                state.lbl_status.config(text=f"🎯 Đã gặt xong {step_title}!", fg="green")
                return True

        time.sleep(0.05)

    pydirectinput.keyUp(alt_key)
    return False

def _run_fishing_cycle(sct):
    state.lbl_status.config(text=f"Quăng cần ô số {state.rod_slot}!", fg="blue")
    press_rod_slot()
    if not wait_seconds(config.WAIT_AFTER_CAST_SEC, lambda r: f"Đang chờ cá cắn câu, còn {r}s"):
        return False
    state.lbl_status.config(text="ĐANG BẮT ĐẦU CÂU CÁ...", fg="green")
    if not fight_minigame(sct): return False
    state.lbl_status.config(text=f"Sắp quăng lại ô {state.rod_slot}...", fg="blue")
    return True

def _run_alt_target_cycle(sct, job):
    menu_pos = job.get("menu_pos")
    is_step_1 = (state.alt_target_phase == "step_1")
    
    is_crab = "cua" in job["name"].lower() or "crab" in job["name"].lower()
    
    # ====================================================================
    # 🧠 PHÂN RÃ THỜI GIAN ĐỘNG v5.1 (FIX CHUẨN SAN HÔ 10s - 5s)
    # ====================================================================
    if is_crab:
        # 🦀 Nghề Cua: Bước 1 xài giờ Đạo cụ, Bước 2 mặc định 5s
        work_sec = config.TOOL_TIERS.get(state.active_tool_tier, 15) if is_step_1 else 5
    else:
        # 🪸 Nghề San Hô (hoặc các nghề tay khum tương tự): Bước 1 vĩnh viễn 10s, Bước 2 vĩnh viễn 5s
        work_sec = 10 if is_step_1 else 5
    # ====================================================================
    
    tpl = job["step_1_tpl"] if is_step_1 else job["step_2_tpl"]
    phase_title = "Bước 1 (Thu hoạch)" if is_step_1 else "Bước 2 (Chế biến)"
    
    state.lbl_status.config(text=f"Đang rình {job['name']} - [{phase_title}]...", fg="blue")

    if execute_alt_step(sct, tpl, phase_title, menu_click_pos=menu_pos):
        if not wait_seconds(
            work_sec, 
            lambda r: f"Đang cày {phase_title} ({work_sec}s)... còn {r}s"
        ):
            return False
        
        time.sleep(random.uniform(0.8, 1.5))
        
    return state.bot_running

def master_worker_loop():
    load_templates()
    for i in range(config.FOCUS_COUNTDOWN_SEC, 0, -1):
        if not state.bot_running: return
        state.lbl_status.config(text=f"Mở game lẹ! Bot chạy sau {i}s...", fg="red")
        time.sleep(1)

    with mss.mss() as sct:
        while state.bot_running:
            job = config.JOB_REGISTRY[state.active_job_id]
            if job["type"] == "fishing":
                if not _run_fishing_cycle(sct): break
            elif job["type"] == "alt_target":
                if not _run_alt_target_cycle(sct, job): break