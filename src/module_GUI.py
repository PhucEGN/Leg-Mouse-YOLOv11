import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import yaml

YAML_PATH = "src/asset/config/config.YAML"   # <- use same filename as main/control

class GUI_frame:
    def __init__(self, root, frame_queue, scale=0.5, control_queue=None):
        self.root = root
        self.root.title("Foot Mouse Control")
        self.root.geometry("1200x650")
        self.root.configure(bg="#f0f0f0")

        self.control_queue = control_queue

        # Giao diện dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ==== Tiêu đề ====
        title = ctk.CTkLabel(root, text="Leg Mouse", font=("Arial", 24, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(20, 10))

        # ==== Biến chứa video ====
        self.frame_queue = frame_queue
        self.frame = None

        # ==== Frame chứa video ====
        self.frame_video = ctk.CTkFrame(root, width=640, height=480, corner_radius=10)
        self.frame_video.grid(row=1, column=0, padx=5, pady=5)
        self.frame_video.grid_propagate(False)
        self.video_label = ctk.CTkLabel(self.frame_video, text="", font=("Arial", 18))
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        # ==== Frame Mouse Control ====
        self.frame_mouse_control = ctk.CTkFrame(root, width=500, height=480, corner_radius=10)
        self.frame_mouse_control.grid(row=1, column=1, padx=5, pady=5)
        self.frame_mouse_control.grid_propagate(False)

        # Add Flip Camera button
        self.flip_button = ctk.CTkButton(
            self.frame_mouse_control,
            text="Flip Camera",
            width=120,
            height=30,
            command=self.toggle_flip
        )
        self.flip_button.place(relx=0.5, rely=0.95, anchor="center")

        # Add flip state variable
        self.is_flipped = False

        title_mouse_control = ctk.CTkLabel(self.frame_mouse_control, text="CLICK ZONE CONTROL", font=("Arial", 18, "bold"))
        title_mouse_control.place(relx=0.5, rely=0.08, anchor="center")
        title_area_control = ctk.CTkLabel(self.frame_mouse_control, text="AREA CONTROL", font=("Arial", 18, "bold"))
        title_area_control.place(relx=0.5, rely=0.43, anchor="center")

        # ==== Đọc giá trị từ YAML ====
        x1, x2, y1, y2, x1_click, x2_click, y1_click, y2_click, flip_state = self.Read_YAML()

        # ==== Biến điều khiển ====
        self.x1_click = x1_click
        self.x2_click = x2_click
        self.y1_click = y1_click
        self.y2_click = y2_click

        self.x1_val = x1
        self.x2_val = x2
        self.y1_val = y1
        self.y2_val = y2

        # set flip initial from YAML
        self.is_flipped = bool(flip_state)
        self.flip_button.configure(text=f"Flip Camera: {'ON' if self.is_flipped else 'OFF'}")

        self.save_job_id = None
        self.SAVE_DELAY_MS = 2000 # 5 giây
        
        # ==== Label tiêu đề cho vùng click ====
        title_x1_click = ctk.CTkLabel(self.frame_mouse_control, text="x1:", font=("Arial", 16, "bold"))
        title_x1_click.place(relx=0.05, rely=0.15, anchor="center")
        title_x2_click = ctk.CTkLabel(self.frame_mouse_control, text="x2:", font=("Arial", 16, "bold"))
        title_x2_click.place(relx=0.05, rely=0.23, anchor="center")
        title_y1_click = ctk.CTkLabel(self.frame_mouse_control, text="y1:", font=("Arial", 16, "bold"))
        title_y1_click.place(relx=0.6, rely=0.15, anchor="center")
        title_y2_click = ctk.CTkLabel(self.frame_mouse_control, text="y2:", font=("Arial", 16, "bold"))
        title_y2_click.place(relx=0.6, rely=0.23, anchor="center")

        # ==== Label hiển thị giá trị vùng click ====
        self.value_x1_click = ctk.CTkLabel(self.frame_mouse_control, text=str(self.x1_click), font=("Arial", 16, "bold"))
        self.value_x1_click.place(relx=0.25, rely=0.15, anchor="center")
        self.value_x2_click = ctk.CTkLabel(self.frame_mouse_control, text=str(self.x2_click), font=("Arial", 16, "bold"))
        self.value_x2_click.place(relx=0.25, rely=0.23, anchor="center")
        self.value_y1_click = ctk.CTkLabel(self.frame_mouse_control, text=str(self.y1_click), font=("Arial", 16, "bold"))
        self.value_y1_click.place(relx=0.8, rely=0.15, anchor="center")
        self.value_y2_click = ctk.CTkLabel(self.frame_mouse_control, text=str(self.y2_click), font=("Arial", 16, "bold"))
        self.value_y2_click.place(relx=0.8, rely=0.23, anchor="center")

        # ==== Nút điều chỉnh vùng click ====
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_click_zone("x1", 2)).place(relx=0.35, rely=0.15, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_click_zone("x1", -2)).place(relx=0.15, rely=0.15, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_click_zone("x2", 2)).place(relx=0.35, rely=0.23, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_click_zone("x2", -2)).place(relx=0.15, rely=0.23, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_click_zone("y1", 2)).place(relx=0.9, rely=0.15, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_click_zone("y1", -2)).place(relx=0.7, rely=0.15, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_click_zone("y2", 2)).place(relx=0.9, rely=0.23, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_click_zone("y2", -2)).place(relx=0.7, rely=0.23, anchor="center")

        # ==== Label tiêu đề cho vùng điều khiển ====
        title_x1 = ctk.CTkLabel(self.frame_mouse_control, text="x1:", font=("Arial", 16, "bold"))
        title_x1.place(relx=0.05, rely=0.53, anchor="center")
        title_x2 = ctk.CTkLabel(self.frame_mouse_control, text="x2:", font=("Arial", 16, "bold"))
        title_x2.place(relx=0.05, rely=0.63, anchor="center")
        title_y1 = ctk.CTkLabel(self.frame_mouse_control, text="y1:", font=("Arial", 16, "bold"))
        title_y1.place(relx=0.6, rely=0.53, anchor="center")
        title_y2 = ctk.CTkLabel(self.frame_mouse_control, text="y2:", font=("Arial", 16, "bold"))
        title_y2.place(relx=0.6, rely=0.63, anchor="center")

        # ==== Label hiển thị giá trị vùng điều khiển ====
        self.value_x1 = ctk.CTkLabel(self.frame_mouse_control, text=str(self.x1_val), font=("Arial", 16, "bold"))
        self.value_x1.place(relx=0.25, rely=0.53, anchor="center")
        self.value_x2 = ctk.CTkLabel(self.frame_mouse_control, text=str(self.x2_val), font=("Arial", 16, "bold"))
        self.value_x2.place(relx=0.25, rely=0.63, anchor="center")
        self.value_y1 = ctk.CTkLabel(self.frame_mouse_control, text=str(self.y1_val), font=("Arial", 16, "bold"))
        self.value_y1.place(relx=0.8, rely=0.53, anchor="center")
        self.value_y2 = ctk.CTkLabel(self.frame_mouse_control, text=str(self.y2_val), font=("Arial", 16, "bold"))
        self.value_y2.place(relx=0.8, rely=0.63, anchor="center")

        # ==== Nút điều chỉnh vùng điều khiển ====
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_value("x1", 2)).place(relx=0.35, rely=0.53, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_value("x1", -2)).place(relx=0.15, rely=0.53, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_value("x2", 2)).place(relx=0.35, rely=0.63, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_value("x2", -2)).place(relx=0.15, rely=0.63, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_value("y1", 2)).place(relx=0.9, rely=0.53, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_value("y1", -2)).place(relx=0.7, rely=0.53, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="+", width=30, command=lambda: self.change_value("y2", 2)).place(relx=0.9, rely=0.63, anchor="center")
        ctk.CTkButton(self.frame_mouse_control, text="-", width=30, command=lambda: self.change_value("y2", -2)).place(relx=0.7, rely=0.63, anchor="center")

        # Thay đổi biến theo dõi trạng thái
        self.is_minimized = False
        self.popup_window = None
        self.popup_scale = scale  # Scale 50% kích thước gốc
        
        # Bind các sự kiện window
        self.root.bind("<FocusOut>", self.handle_focus_lost)
        self.root.bind("<FocusIn>", self.handle_focus_gained)
        self.root.bind("<Unmap>", self.handle_minimize)
        self.root.bind("<Map>", self.handle_restore)
        
        # ==== Bắt đầu update video ====
        self.update_video()
        if self.control_queue is not None:
            self.periodic_send()

    # ==== Hàm thay đổi vùng click ====
    def change_click_zone(self, var_name, delta):
        if var_name == "x1":
            self.x1_click = max(0, min(640, self.x1_click + delta))
            self.value_x1_click.configure(text=str(self.x1_click))
        elif var_name == "x2":
            self.x2_click = max(0, min(640, self.x2_click + delta))
            self.value_x2_click.configure(text=str(self.x2_click))
        elif var_name == "y1":
            self.y1_click = max(0, min(480, self.y1_click + delta))
            self.value_y1_click.configure(text=str(self.y1_click))
        elif var_name == "y2":
            self.y2_click = max(0, min(480, self.y2_click + delta))
            self.value_y2_click.configure(text=str(self.y2_click))
        self.send_data_to_queue()
        self.schedule_yaml_save()
        
    # ==== Hàm thay đổi vùng điều khiển ====
    def change_value(self, var_name, delta):
        if var_name == "x1":
            self.x1_val = max(0, min(640, self.x1_val + delta))
            self.value_x1.configure(text=str(self.x1_val))
        elif var_name == "x2":
            self.x2_val = max(0, min(640, self.x2_val + delta))
            self.value_x2.configure(text=str(self.x2_val))
        elif var_name == "y1":
            self.y1_val = max(0, min(480, self.y1_val + delta))
            self.value_y1.configure(text=str(self.y1_val))
        elif var_name == "y2":
            self.y2_val = max(0, min(480, self.y2_val + delta))
            self.value_y2.configure(text=str(self.y2_val))
        self.send_data_to_queue()
        self.schedule_yaml_save()

    # ==== Gửi dữ liệu ====
    def send_data(self):
        click_zone = {
            "x1": self.x1_click,
            "x2": self.x2_click,
            "y1": self.y1_click,
            "y2": self.y2_click
        }
        rec_area = [self.x1_val, self.x2_val, self.y1_val, self.y2_val]
        # Add flip state to sent data
        return click_zone, rec_area, self.is_flipped

    # ==== Đọc YAML ====
    def Read_YAML(self):
        try:
            with open(YAML_PATH, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
        except FileNotFoundError:
            data = {}

        click_zone = data.get("Click_zone", {})
        rec = data.get("Rec_area", {})
        flip_state = data.get("Flip", False)

        return (
            rec.get("x1", 0), rec.get("x2", 0),
            rec.get("y1", 0), rec.get("y2", 0),
            click_zone.get("x1", 0), click_zone.get("x2", 0),
            click_zone.get("y1", 0), click_zone.get("y2", 0),
            flip_state
        )

    def Write_YAML(self):
        """Ghi các giá trị điều khiển hiện tại vào file YAML."""
        try:
            # Bước 1: Đọc toàn bộ file để giữ lại các mục khác (ví dụ: ColorRange)
            try:
                with open(YAML_PATH, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except FileNotFoundError:
                data = {}
            
            # Bước 2: Cập nhật các mục Rec_area, Click_zone, và Flip
            data["Rec_area"] = {
                "x1": int(self.x1_val), "x2": int(self.x2_val), 
                "y1": int(self.y1_val), "y2": int(self.y2_val)
            }
            data["Click_zone"] = {
                "x1": int(self.x1_click), "x2": int(self.x2_click), 
                "y1": int(self.y1_click), "y2": int(self.y2_click)
            }
            data["Flip"] = bool(self.is_flipped)
            
            # Bước 3: Ghi dữ liệu đã cập nhật trở lại file
            with open(YAML_PATH, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True)
                
            print("Cấu hình đã được lưu vào CONFIG.YAML")
            
        except Exception as e:
            print(f"Lỗi khi ghi YAML: {e}")
    
    def schedule_yaml_save(self):
        """Hủy bỏ tác vụ lưu trước đó và lên lịch tác vụ lưu mới."""
        # Hủy tác vụ lưu trước đó nếu có
        if self.save_job_id:
            self.root.after_cancel(self.save_job_id)
        
        # Lên lịch tác vụ lưu mới sau 5 giây
        self.save_job_id = self.root.after(self.SAVE_DELAY_MS, self.Write_YAML)
          
    # ==== Gửi queue định kỳ ====
    def send_data_to_queue(self):
        if self.control_queue is None:
            return
        data = self.send_data()
        try:
            if self.control_queue.full():
                self.control_queue.get_nowait()
            self.control_queue.put_nowait(data)
        except:
            pass

    def periodic_send(self):
        self.send_data_to_queue()
        self.root.after(500, self.periodic_send)

    # ==== Cập nhật video ====
    def get_frame(self, frame):
        self.frame = frame

    def create_popup(self):
        """Tạo cửa sổ popup"""
        if self.popup_window is None:
            self.popup_window = ctk.CTkToplevel()
            self.popup_window.title("Camera Preview")
            
            # Calculate scaled dimensions
            scaled_w = int(640 * self.popup_scale)
            scaled_h = int(480 * self.popup_scale)
            
            # Create frame
            self.popup_frame = ctk.CTkFrame(
                self.popup_window, 
                width=scaled_w,
                height=scaled_h,
                fg_color="black"
            )
            self.popup_frame.pack(padx=5, pady=5)
            self.popup_frame.pack_propagate(False)
            
            # Create label for video
            self.popup_label = ctk.CTkLabel(
                self.popup_frame,
                text="",
                fg_color="black"
            )
            self.popup_label.place(relx=0.5, rely=0.5, anchor="center")
            
            # Position window
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = screen_w - scaled_w - 20
            y = screen_h - scaled_h - 60
            self.popup_window.geometry(f"{scaled_w}x{scaled_h}+{x}+{y}")
            
            # Window attributes
            self.popup_window.attributes('-topmost', True)
            self.popup_window.overrideredirect(True)
            self.popup_window.resizable(False, False)
            
            # Bind events for dragging
            self.popup_label.bind("<Button-1>", self.start_move)
            self.popup_label.bind("<B1-Motion>", self.do_move)
            self.popup_label.bind("<ButtonRelease-1>", self.stop_move)
            self.popup_label.bind("<Double-Button-1>", self.handle_popup_click)
            
            # Track window position
            self.drag_data = {"x": 0, "y": 0, "dragging": False}

    def start_move(self, event):
        """Bắt đầu di chuyển popup"""
        if not self.drag_data["dragging"]:
            self.drag_data["x"] = event.x_root
            self.drag_data["y"] = event.y_root
            self.drag_data["dragging"] = True

    def do_move(self, event):
        """Di chuyển popup theo chuột"""
        if self.drag_data["dragging"]:
            # Calculate distance moved
            delta_x = event.x_root - self.drag_data["x"]
            delta_y = event.y_root - self.drag_data["y"]
            
            # Get current position
            x = self.popup_window.winfo_x() + delta_x
            y = self.popup_window.winfo_y() + delta_y
            
            # Move window
            self.popup_window.geometry(f"+{x}+{y}")
            
            # Update reference point
            self.drag_data["x"] = event.x_root
            self.drag_data["y"] = event.y_root

    def stop_move(self, event):
        """Kết thúc di chuyển popup"""
        self.drag_data["dragging"] = False

    def handle_focus_lost(self, event=None):
        """Xử lý khi cửa sổ chính mất focus"""
        if not self.is_minimized and not self.popup_window:
            self.create_popup()
            self.is_minimized = True

    def handle_focus_gained(self, event=None):
        """Xử lý khi cửa sổ chính được focus"""
        if self.is_minimized and self.popup_window:
            self.handle_popup_close()

    def handle_popup_click(self, event=None):
        """Xử lý khi click vào popup"""
        self.handle_popup_close()
        self.root.deiconify()
        self.root.focus_force()

    def handle_popup_close(self):
        """Xử lý khi đóng popup window"""
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
        self.is_minimized = False
        # Restore và focus cửa sổ chính
        self.root.deiconify()
        self.root.focus_force()

    def handle_minimize(self, event=None):
        """Xử lý khi cửa sổ chính bị minimize"""
        if not self.is_minimized and not self.popup_window:
            self.create_popup()
            self.is_minimized = True
            # Hide main window
            self.root.withdraw()

    def handle_restore(self, event=None):
        """Xử lý khi cửa sổ chính được restore"""
        if self.is_minimized and self.popup_window:
            self.handle_popup_close()
        # Show main window
        self.root.deiconify()
        self.is_minimized = False

    def update_video(self):
        while not self.frame_queue.empty():
            self.frame = self.frame_queue.get()
        
        if self.frame is not None:
            # Convert frame to PIL Image
            img = Image.fromarray(self.frame)
            
            # Update main window
            main_img = ctk.CTkImage(
                light_image=img, 
                dark_image=img,
                size=(640, 480)
            )
            self.video_label.configure(image=main_img)
            self.video_label.image = main_img
            
            # Update popup if exists
            if self.popup_window and self.is_minimized:
                # Calculate scaled dimensions
                scaled_w = int(640 * self.popup_scale)
                scaled_h = int(480 * self.popup_scale)
                
                # Create scaled image for popup
                popup_img = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(scaled_w, scaled_h)
                )
                
                # Update popup label with scaled image
                if hasattr(self, 'popup_label'):
                    self.popup_label.configure(image=popup_img)
                    self.popup_label.image = popup_img  # Keep reference
                
        # Schedule next update
        self.root.after(10, self.update_video)

    def _draw_areas_on_popup(self):
        """Vẽ các vùng điều khiển đã scale lên popup"""
        if not self.popup_window or not self.popup_label.image:
            return
            
        # Lấy kích thước scaled
        scaled_w = int(640 * self.popup_scale)
        scaled_h = int(480 * self.popup_scale)
        
        # Scale các tọa độ để vẽ (chỉ để hiển thị)
        def scale_coord(x, y):
            return (
                int(x * self.popup_scale),
                int(y * self.popup_scale)
            )
        
        # Tạo overlay image để vẽ
        overlay = Image.new('RGBA', (scaled_w, scaled_h), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        # Vẽ vùng điều khiển (đỏ)
        x1, y1 = scale_coord(self.x1_val, self.y1_val)
        x2, y2 = scale_coord(self.x2_val, self.y2_val)
        draw.rectangle([x1,y1,x2,y2], outline='red', width=2)
        
        # Vẽ vùng click (xanh)
        x1, y1 = scale_coord(self.x1_click, self.y1_click)
        x2, y2 = scale_coord(self.x2_click, self.y2_click)
        draw.rectangle([x1,y1,x2,y2], outline='blue', width=2)
        
        # Kết hợp với frame gốc
        if isinstance(self.popup_label.image, ctk.CTkImage):
            frame = self.popup_label.image._light_image
            result = Image.alpha_composite(frame.convert('RGBA'), overlay)
            
            popup_img = ctk.CTkImage(
                light_image=result,
                dark_image=result,
                size=(scaled_w, scaled_h)
            )
            self.popup_label.configure(image=popup_img)
            self.popup_label.image = popup_img

    def toggle_flip(self):
        """Toggle camera flip state and send to control process"""
        self.is_flipped = not self.is_flipped
        self.flip_button.configure(text=f"Flip Camera: {'ON' if self.is_flipped else 'OFF'}")
        self.send_data_to_queue()
        self.schedule_yaml_save()