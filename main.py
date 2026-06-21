import os
import threading
import time

import customtkinter as ctk
import keyboard
import mss

import modules.config as config
import modules.state as state
from modules.controls import clear_keys, fight_minigame, press_rod_slot, wait_seconds
from modules.vision import load_templates, resource_path

# ==========================================
# 🖥️ GIAO DIỆN PREMIUM MODERN (CUSTOMTKINTER)
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StatusLabelAdapter:
    def __init__(self, widget):
        self._widget = widget

    def config(self, **kwargs):
        color_map = {
            "red": "#ED4245",
            "blue": "#00B4D8",
            "green": "#3BA55C",
            "orange": "#FEE75C",
            "black": "#A1A1AA"
        }
        if 'fg' in kwargs:
            kwargs['text_color'] = color_map.get(kwargs.pop('fg'), "#E4E4E7")

        def _apply():
            self._widget.configure(**kwargs)

        self._widget.after(0, _apply)

    def configure(self, **kwargs):
        def _apply():
            self._widget.configure(**kwargs)

        self._widget.after(0, _apply)


def auto_fishing_loop():
    # Load ảnh mẫu vào RAM trước khi chiến
    load_templates()

    for i in range(config.FOCUS_COUNTDOWN_SEC, 0, -1):
        if not state.bot_running: return
        state.lbl_status.config(text=f"Mở game lẹ! Bot chạy sau {i}s...", fg="red")
        time.sleep(1)

    with mss.MSS() as sct:
        while state.bot_running:
            state.lbl_status.config(text=f"Quăng cần ô số {state.rod_slot}!", fg="blue")
            press_rod_slot()

            if not wait_seconds(
                config.WAIT_AFTER_CAST_SEC,
                lambda remaining: f"Đang chờ cá cắn câu, còn {remaining}s",
            ):
                break

            state.lbl_status.config(text="ĐANG BẮT ĐẦU CÂU CÁ...", fg="green")

            if not fight_minigame(sct):
                break

            state.lbl_status.config(text=f"Sắp quăng lại ô {state.rod_slot}...", fg="blue")


def start_bot():
    if not state.bot_running:
        state.bot_running = True
        state.bot_paused = False
        state.rod_slot = combo_slot.get()

        btn_start.configure(state="disabled", fg_color="#383A40")
        btn_pause.configure(state="normal", text="TẠM DỪNG (F6)", fg_color="#4F545C", hover_color="#686D73", text_color="#FFFFFF")
        btn_stop.configure(state="normal")
        combo_slot.configure(state="disabled")

        t = threading.Thread(target=auto_fishing_loop)
        t.daemon = True
        t.start()


def toggle_pause():
    if state.bot_running:
        state.bot_paused = not state.bot_paused
        if state.bot_paused:
            clear_keys()
            btn_pause.configure(text="TIẾP TỤC (F6)", fg_color="#FEE75C", hover_color="#D4C14A", text_color="#18181B")
            state.lbl_status.config(text="Đã TẠM DỪNG. Lượn phố thôi!", fg="orange")
        else:
            btn_pause.configure(text="TẠM DỪNG (F6)", fg_color="#4F545C", hover_color="#686D73", text_color="#FFFFFF")
            state.lbl_status.config(text="Tiếp tục quăng cần! Cày tiền thôi!", fg="green")


def stop_bot():
    state.bot_running = False
    state.bot_paused = False
    clear_keys()

    btn_start.configure(state="normal", fg_color="#5865F2")
    btn_pause.configure(state="disabled", text="TẠM DỪNG (F6)", fg_color="#383A40")
    btn_stop.configure(state="disabled")
    combo_slot.configure(state="readonly")
    state.lbl_status.config(text="Đã tắt Bot hoàn toàn.", fg="red")


keyboard.add_hotkey("f6", toggle_pause)

root = ctk.CTk()
root.title("CC anh Phúc lập trình ziên")
root.iconbitmap(resource_path(os.path.join("assets", "logo.ico")))
root.geometry("360x250")
root.attributes("-topmost", True)
root.configure(fg_color="#18181B")

lbl_title = ctk.CTkLabel(root, text="CHỌN Ô CẦN CÂU (1-5)", font=("Segoe UI", 13, "bold"), text_color="#E4E4E7")
lbl_title.pack(pady=(20, 10))

combo_slot = ctk.CTkComboBox(root, values=["1", "2", "3", "4", "5"], width=130, height=32,
                             fg_color="#2B2D31", border_color="#383A40",
                             button_color="#383A40", button_hover_color="#4F545C",
                             dropdown_fg_color="#2B2D31", dropdown_text_color="#E4E4E7",
                             text_color="#E4E4E7", font=("Segoe UI", 14, "bold"), state="readonly")
combo_slot.set("1")
combo_slot.pack(pady=(0, 20))

frame_btn = ctk.CTkFrame(root, fg_color="transparent")
frame_btn.pack(pady=5)

btn_start = ctk.CTkButton(frame_btn, text="▶ BẬT BOT", width=80, height=35, corner_radius=6,
                          fg_color="#5865F2", hover_color="#4752C4",
                          font=("Segoe UI", 12, "bold"), command=start_bot)
btn_start.grid(row=0, column=0, padx=8)

btn_pause = ctk.CTkButton(frame_btn, text="⏸TẠM DỪNG (F6)", width=110, height=35, corner_radius=6,
                          fg_color="#383A40", hover_color="#4F545C",
                          font=("Segoe UI", 12, "bold"), command=toggle_pause, state="disabled")
btn_pause.grid(row=0, column=1, padx=8)

btn_stop = ctk.CTkButton(frame_btn, text="❌TẮT", width=60, height=35, corner_radius=6,
                         fg_color="#ED4245", hover_color="#C9383A",
                         font=("Segoe UI", 12, "bold"), command=stop_bot, state="disabled")
btn_stop.grid(row=0, column=2, padx=8)

_status_widget = ctk.CTkLabel(root, text="Bắt đầu treo thoiiii", font=("Segoe UI", 13, "italic"), text_color="#A1A1AA")
_status_widget.pack(pady=(15, 0))
lbl_status = StatusLabelAdapter(_status_widget)
state.lbl_status = lbl_status

root.mainloop()
