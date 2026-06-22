import os
import threading
import customtkinter as ctk
import keyboard
import modules.config as config
import modules.state as state
from modules.controls import clear_keys, master_worker_loop
from modules.vision import resource_path

# ==========================================
# 🖥️ GIAO DIỆN PREMIUM MODERN (v5.0 AUTO-RESIZE)
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

JOB_DISPLAY_TO_ID = {job["name"]: job_id for job_id, job in config.JOB_REGISTRY.items()}
PHASE_DISPLAY_TO_ID = {
    "Phase 1: Thu Hoạch": "step_1",
    "Phase 2: Chế Biến": "step_2",
}
PHASE_ID_TO_DISPLAY = {v: k for k, v in PHASE_DISPLAY_TO_ID.items()}

COMBO_STYLE_FIXED = {
    "height": 32,
    "fg_color": "#2B2D31",
    "border_color": "#383A40",
    "button_color": "#383A40",
    "button_hover_color": "#4F545C",
    "dropdown_fg_color": "#2B2D31",
    "dropdown_text_color": "#E4E4E7",
    "text_color": "#E4E4E7",
    "font": ("Segoe UI", 13, "bold"),
}

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


# ==========================================
# 🧠 TRẠM KIỂM SOÁT GIAO DIỆN ĐỘNG v5.0
# ==========================================
def update_ui_visibility():
    job_name = combo_job.get()
    job_id = JOB_DISPLAY_TO_ID[job_name]
    phase_id = PHASE_DISPLAY_TO_ID[seg_phase.get()]

    # 1. Thu hồi tất cả các Frame động vào chuồng gà
    frame_tool.grid_forget()
    frame_phase.grid_forget()
    frame_slot.grid_forget()

    dynamic_container.rowconfigure(0, weight=0)
    dynamic_container.rowconfigure(1, weight=0)
    dynamic_container.rowconfigure(2, weight=0)

    # 2. Bày binh bố trận lại theo đúng Logic
    if job_id == "fishing":
        # Nghề cá: Chỉ hiện Cần câu
        frame_slot.grid(row=0, column=0, sticky="nsew", pady=10)
        dynamic_container.rowconfigure(0, weight=1)
    else:
        # Nghề Cao Su (San hô / Cua)
        current_row = 0
        
        # Phase Segment luôn luôn hiện khi không phải câu cá
        frame_phase.grid(row=current_row, column=0, sticky="nsew", pady=10)
        dynamic_container.rowconfigure(current_row, weight=1)
        current_row += 1

        # 🧠 THẦN CHÚ V5.0: Chỉ hiện ô Đạo Cụ khi tên nghề có chữ "Cua" và đang ở Pha 1!
        is_crab = "cua" in job_name.lower() or "crab" in job_name.lower()
        if is_crab and phase_id == "step_1":
            frame_tool.grid(row=current_row, column=0, sticky="nsew", pady=10)
            dynamic_container.rowconfigure(current_row, weight=1)

    # ⚡ ÉP CỬA SỔ ÔM KHÍT NỘI DUNG THỰC TẾ
    root.update_idletasks()
    req_height = root.winfo_reqheight()
    root.geometry(f"420x{req_height}")


# ==========================================
# 🎮 CÁC HÀM XỬ LÝ SỰ KIỆN
# ==========================================
def on_tool_selected(choice):
    state.active_tool_tier = choice

def on_phase_selected(value):
    state.alt_target_phase = PHASE_DISPLAY_TO_ID[value]
    update_ui_visibility()

def on_job_selected(choice):
    state.active_job_id = JOB_DISPLAY_TO_ID[choice]
    update_ui_visibility()

def start_bot():
    if not state.bot_running:
        state.bot_running = True
        state.bot_paused = False
        state.active_job_id = JOB_DISPLAY_TO_ID[combo_job.get()]
        state.rod_slot = combo_slot.get()
        state.active_tool_tier = combo_tool.get()
        state.alt_target_phase = PHASE_DISPLAY_TO_ID[seg_phase.get()]

        btn_start.configure(state="disabled", fg_color="#383A40")
        btn_pause.configure(state="normal", text="TẠM DỪNG (F6)", fg_color="#4F545C", hover_color="#686D73", text_color="#FFFFFF")
        btn_stop.configure(state="normal")
        combo_job.configure(state="disabled")
        combo_slot.configure(state="disabled")
        combo_tool.configure(state="disabled")
        seg_phase.configure(state="disabled")

        t = threading.Thread(target=master_worker_loop)
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
            state.lbl_status.config(text="Tiếp tục cày cuốc!", fg="green")

def stop_bot():
    state.bot_running = False
    state.bot_paused = False
    clear_keys()

    btn_start.configure(state="normal", fg_color="#5865F2")
    btn_pause.configure(state="disabled", text="TẠM DỪNG (F6)", fg_color="#383A40")
    btn_stop.configure(state="disabled")
    combo_job.configure(state="readonly")
    combo_slot.configure(state="readonly")
    combo_tool.configure(state="readonly")
    seg_phase.configure(state="normal")
    
    state.lbl_status.config(text="Đã tắt Bot hoàn toàn.", fg="red")


keyboard.add_hotkey("f6", toggle_pause)

# ==========================================
# 🏗️ DỰNG HÌNH KHUNG GIAO DIỆN (WIDGETS)
# ==========================================
root = ctk.CTk()
root.title("CC anh Phúc lập trình diên v5.0")
root.iconbitmap(resource_path(os.path.join("assets", "logo.ico")))

root.geometry("420x400") 
root.attributes("-topmost", True)
root.configure(fg_color="#18181B")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=0)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=0)
root.rowconfigure(3, weight=0)


# --- 1. HÀNG HEADER (CHỌN NGHỀ NGHIỆP) ---
frame_job_header = ctk.CTkFrame(root, fg_color="transparent")
frame_job_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
frame_job_header.columnconfigure(0, weight=1)

lbl_job = ctk.CTkLabel(frame_job_header, text="CHỌN NGHỀ NGHIỆP", font=("Segoe UI", 13, "bold"), text_color="#E4E4E7")
lbl_job.grid(row=0, column=0, pady=(0, 8))

combo_job = ctk.CTkComboBox(frame_job_header, values=[job["name"] for job in config.JOB_REGISTRY.values()], state="readonly", command=on_job_selected, **COMBO_STYLE_FIXED)
combo_job.set(config.JOB_REGISTRY["fishing"]["name"])
combo_job.grid(row=1, column=0, sticky="ew")


# --- 2. HÀNG GIỮA DYNAMIC CONTAINER ---
dynamic_container = ctk.CTkFrame(root, fg_color="transparent")
dynamic_container.grid(row=1, column=0, sticky="nsew", padx=20)
dynamic_container.columnconfigure(0, weight=1)

# SUB-FRAME: ĐẠO CỤ
frame_tool = ctk.CTkFrame(dynamic_container, fg_color="transparent")
frame_tool.columnconfigure(0, weight=1)
lbl_tool = ctk.CTkLabel(frame_tool, text="CHỌN CẤP ĐẠO CỤ", font=("Segoe UI", 13, "bold"), text_color="#E4E4E7")
lbl_tool.grid(row=0, column=0, pady=(0, 8))
combo_tool = ctk.CTkComboBox(frame_tool, values=list(config.TOOL_TIERS.keys()), state="readonly", command=on_tool_selected, **COMBO_STYLE_FIXED)
combo_tool.set(state.active_tool_tier)
combo_tool.grid(row=1, column=0, sticky="ew")

# SUB-FRAME: PHA GẶT
frame_phase = ctk.CTkFrame(dynamic_container, fg_color="transparent")
frame_phase.columnconfigure(0, weight=1)
lbl_phase = ctk.CTkLabel(frame_phase, text="CHỌN PHA GẶT LÔ", font=("Segoe UI", 13, "bold"), text_color="#E4E4E7")
lbl_phase.grid(row=0, column=0, pady=(0, 8))
seg_phase = ctk.CTkSegmentedButton(
    frame_phase, values=list(PHASE_DISPLAY_TO_ID.keys()), command=on_phase_selected,
    font=("Segoe UI", 11, "bold"), fg_color="#2B2D31", selected_color="#5865F2",
    selected_hover_color="#4752C4", unselected_color="#383A40", unselected_hover_color="#4F545C",
    text_color="#E4E4E7", state="normal", height=32
)
seg_phase.set(PHASE_ID_TO_DISPLAY[state.alt_target_phase])
seg_phase.grid(row=1, column=0, sticky="ew")

# SUB-FRAME: SLOT CẦN CÂU
frame_slot = ctk.CTkFrame(dynamic_container, fg_color="transparent")
frame_slot.columnconfigure(0, weight=1)
lbl_title = ctk.CTkLabel(frame_slot, text="CHỌN Ô CẦN CÂU (1-5)", font=("Segoe UI", 13, "bold"), text_color="#E4E4E7")
lbl_title.grid(row=0, column=0, pady=(0, 8))
combo_slot = ctk.CTkComboBox(
    frame_slot, values=["1", "2", "3", "4", "5"], height=32,
    fg_color="#2B2D31", border_color="#383A40", button_color="#383A40", button_hover_color="#4F545C",
    dropdown_fg_color="#2B2D31", dropdown_text_color="#E4E4E7", text_color="#E4E4E7",
    font=("Segoe UI", 14, "bold"), state="readonly"
)
combo_slot.set("1")
combo_slot.grid(row=1, column=0)


# --- 3. HÀNG FOOTER (NÚT BẤM) ---
frame_btn = ctk.CTkFrame(root, fg_color="transparent")
frame_btn.grid(row=2, column=0, sticky="ew", padx=20, pady=(15, 5))
frame_btn.columnconfigure(0, weight=1)
frame_btn.columnconfigure(1, weight=1)
frame_btn.columnconfigure(2, weight=1)

btn_start = ctk.CTkButton(frame_btn, text="▶ BẬT BOT", height=35, corner_radius=6, fg_color="#5865F2", hover_color="#4752C4", font=("Segoe UI", 12, "bold"), command=start_bot)
btn_start.grid(row=0, column=0, padx=5, sticky="ew")

btn_pause = ctk.CTkButton(frame_btn, text="⏸TẠM (F6)", height=35, corner_radius=6, fg_color="#383A40", hover_color="#4F545C", font=("Segoe UI", 12, "bold"), command=toggle_pause, state="disabled")
btn_pause.grid(row=0, column=1, padx=5, sticky="ew")

btn_stop = ctk.CTkButton(frame_btn, text="❌TẮT", height=35, corner_radius=6, fg_color="#ED4245", hover_color="#C9383A", font=("Segoe UI", 12, "bold"), command=stop_bot, state="disabled")
btn_stop.grid(row=0, column=2, padx=5, sticky="ew")


# --- 4. HÀNG TRẠNG THÁI (STATUS) ---
_status_widget = ctk.CTkLabel(root, text="Hệ thống v5.0 sẵn sàng càn quét!", font=("Segoe UI", 13, "italic"), text_color="#A1A1AA")
_status_widget.grid(row=3, column=0, sticky="ew", pady=(10, 15))
lbl_status = StatusLabelAdapter(_status_widget)
state.lbl_status = lbl_status

# Khởi chạy sắp đặt UI lần đầu tiên
update_ui_visibility()

root.mainloop()