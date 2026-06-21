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
