import numpy as np

# ==========================================
# ⚙️ CẤU HÌNH THÔNG SỐ CỐT LÕI
# ==========================================
monitor = {"top": 850, "left": 660, "width": 600, "height": 180}

# 🌟 VÙNG MẮT PHỤ: Quét ô nút bấm bên trái để đọc đề thi (Z, A, Q, Mũi tên)
prompt_monitor = {"top": 920, "left": 672, "width": 35, "height": 34}

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

TOOL_TIERS = {
    "Dụng cụ Thường": 15,
    "Dụng cụ Cấp 2": 10,
}

# Hộp quét 400x400 nằm ngay chính giữa màn hình Full HD (1920x1080)
CENTER_ROI = {"top": 340, "left": 760, "width": 400, "height": 400}

JOB_REGISTRY = {
    "fishing": {
        "name": "Câu Cá",
        "type": "fishing",
        "slot_based": True
    },
    "coral": {
        "name": "Lặn San Hô",
        "type": "alt_target",
        "step_1_tpl": "tpl_coral_s1.png",
        "step_2_tpl": "tpl_coral_s2.png",
        "work_duration": 15,
        "menu_pos": (1000, 535)
    },
    "crab": {
        "name": "Bắt Cua",
        "type": "alt_target",
        "step_1_tpl": "tpl_crab_s1.png",
        "step_2_tpl": "tpl_crab_s2.png",
        "work_duration": 15,
        "menu_pos": (1000, 535)
    }
}
