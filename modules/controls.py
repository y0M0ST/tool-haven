import random
import time

import pydirectinput

import modules.config as config
import modules.state as state
from modules.vision import scan_fish_bar, identify_key_pair

pydirectinput.PAUSE = 0.0


def clear_keys():
    """ Nhả toàn bộ 8 phím có thể gõ ra để đảm bảo khum bao giờ kẹt phím """
    for k in ["q", "e", "a", "d", "z", "c", "left", "right"]:
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
    """ Chiến thần gõ phím linh hoạt theo biến chốt đơn (Đã tiêm bùa lóng ngóng) """
    
    # 🌟 BÙA NGÁO NGƠ VIP PRO: 1.5% tỷ lệ vấp cỏ ngã sấp mặt
    if random.random() < 0.015:
        clear_keys() # Hoảng loạn vật lý: Buông tay thả hết phao ra!
        
        wrong_key = state.active_key_left if diff > 0 else state.active_key_right
        pydirectinput.keyDown(wrong_key)
        time.sleep(random.uniform(0.04, 0.08)) # Bấm lộn 40-80ms
        pydirectinput.keyUp(wrong_key)
        
        # 🧠 THẦN CHÚ ĂN TIỀN: Não người bị "đứng hình" 120ms - 180ms để nhận ra mình ngu
        time.sleep(random.uniform(0.12, 0.18))
        
        return None # CỰC KỲ QUAN TRỌNG: Rút lui ngay, khum cho chạy tiếp khúc dưới!

    # =========================================================
    # [ KHÚC DƯỚI GIỮ NGUYÊN LOGIC CHIẾN THẦN CỦA ĐẠI GIA ]
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
    state.lbl_status.config(text="Câu xong🎉🎉🎉! Đang cất cá vô túi...", fg="orange")
    recovery_sec = config.RECOVERY_DELAY_SEC + random.uniform(0.1, 0.5)
    return wait_seconds(
        recovery_sec,
        lambda remaining: f"Câu xong🎉🎉🎉! Tự động quăng lại sau {remaining}s...",
    )


def fight_minigame(sct):
    ui_seen = False
    missing_frames = 0
    ui_return_streak = 0
    current_pressed = None
    exam_read = False # Biến khóa: Mẻ lưới này đã đọc đề chưa?

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

            # 🌟 ĐỌC ĐỀ THI (Chỉ quét ảnh đúng 1 lần khi UI vừa sập xuống)
            if not exam_read:
                state.active_key_left, state.active_key_right = identify_key_pair(sct)
                # Đổi tên hiển thị cho đẹp (left/right -> Mũi Tên)
                show_l = "←" if state.active_key_left == "left" else state.active_key_left.upper()
                show_r = "→" if state.active_key_right == "right" else state.active_key_right.upper()
                state.lbl_status.config(text=f"🔥 Chốt cặp phím: [ {show_l} ] - [ {show_r} ]", fg="blue")
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
