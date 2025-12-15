import cv2
import ultralytics
import win32api
import win32con
import yaml
import time
import math
import os
# ==================== CONSTANTS ====================
MODEL_PATH = 'src/asset/model/YOLOv11-215pic.pt'
YAML_CONFIG_PATH = 'src/asset/config/config.yaml'

# ===================================================
# CLASS 1: FOOT DETECTOR (Xử lý hình ảnh & AI)
# ===================================================
class FootDetector:
    def __init__(self, model_path=MODEL_PATH):
        print(f"Loading YOLO model from: {model_path}...")
        self.model = ultralytics.YOLO(model_path)
        print("Model loaded successfully.")

    def detect_foot(self, image):
        """
        Thực hiện nhận diện trên khung hình.
        Tối ưu hóa tốc độ bằng cách resize input về 416x416.
        """
        results = self.model.predict(
            source=image, 
            imgsz=416,  # Tăng tốc độ xử lý
            verbose=False, 
            conf=0.5
        )
        return results


# ===================================================
# CLASS 2: CURSOR CONTROLLER (Điều khiển chuột & Cấu hình)
# ===================================================
class CursorController:
    def __init__(self, config_path=YAML_CONFIG_PATH):
        self.config_path = config_path
        
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
        # --- CẤU HÌNH LÀM MƯỢT (SMOOTHING) ---
        # Hệ số làm mượt (0.0 < alpha <= 1.0)
        # Giá trị càng nhỏ: Chuột càng mượt nhưng có độ trễ (lag).
        # Giá trị càng lớn: Chuột càng nhanh nhưng dễ bị rung.
        # Khuyên dùng: 0.1 đến 0.3
        self.smooth_factor = 0.35
        
        # Ngưỡng chống rung (Pixel): Nếu di chuyển nhỏ hơn mức này -> Bỏ qua
        self.jitter_threshold = 9.0 
        
        # Lưu tọa độ thực tế hiện tại (Float để tính toán chính xác)
        self.curr_x = 0.0
        self.curr_y = 0.0
        
        # Khởi tạo tọa độ chuột hiện tại từ hệ thống
        cur_pos = win32api.GetCursorPos()
        self.curr_x, self.curr_y = float(cur_pos[0]), float(cur_pos[1])

        # --- BIẾN TRẠNG THÁI CLICK/SCROLL ---
        self.click_state = False      
        self.last_box_state = False   
        self.left_state = False       
        self.right_state = False      
        self.holding = False          
        
        self.click_delay = 0.5        
        self.click_lasttime = 0.0

        # --- BIẾN CỜ THEO DÕI ---
        # `has_entered_box`: Đã từng vào vùng click ít nhất một lần
        # `outside_frame`: Đang ở ngoài frame hay không (dùng để reset lại trạng thái khi quay lại)
        self.has_entered_box = False
        self.outside_frame = False
        # cache config file to reduce disk I/O
        self._config_cache = None
        self._config_mtime = None

        # --- BIẾN CỜ THEO DÕI TRẠNG THÁI ---
        self.has_entered_box = False  # Biến cờ để kiểm tra nếu đã vào box

    # --- CÁC HÀM XỬ LÝ CONFIG (GIỮ NGUYÊN) ---
    def _read_config(self):
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            return {}

    def get_limit_box(self, name="Click_zone"):
        config = self._read_config()
        box = config.get(name, {})
        return {
            "x1": box.get('x1', 0), "x2": box.get('x2', 0),
            "y1": box.get('y1', 0), "y2": box.get('y2', 0)
        }

    # --- HÀM DI CHUYỂN CHUỘT (ĐÃ NÂNG CẤP) ---
    def move_cursor(self, box, x, y):
        """
        Di chuyển con trỏ chuột với thuật toán Nội suy (Smoothing).
        """
        x1, x2, y1, y2 = box['x1'], box['x2'], box['y1'], box['y2']
        
        # 1. Giới hạn tọa độ đầu vào trong vùng box
        x_limited = max(x1, min(x, x2))
        y_limited = max(y1, min(y, y2))
        
        # Nếu nằm ngoài vùng giới hạn, không xử lý
        if x_limited <= x1 or x_limited >= x2 or y_limited <= y1 or y_limited >= y2:
            return
        
        box_width = x2 - x1
        box_height = y2 - y1
        if box_width == 0 or box_height == 0: return 

        # 2. Tính tọa độ đích (Target) trên màn hình
        relative_x = (x_limited - x1) / box_width
        relative_y = (y_limited - y1) / box_height
        
        target_x = relative_x * self.screen_w
        target_y = relative_y * self.screen_h

        # --- THUẬT TOÁN LÀM MƯỢT (INTERPOLATION) ---
        
        # Tính khoảng cách giữa vị trí hiện tại và đích
        dist = math.sqrt((target_x - self.curr_x)**2 + (target_y - self.curr_y)**2)
        
        # A. CHỐNG RUNG (Deadzone)
        # Nếu khoảng cách di chuyển quá nhỏ (do nhiễu camera), giữ nguyên vị trí
        if dist < self.jitter_threshold:
            return

        # B. NỘI SUY (Lerp: Linear Interpolation)
        # Công thức: Current = Current + (Target - Current) * Alpha
        
        # (Tùy chọn) Dynamic Smoothing: Di chuyển nhanh thì mượt ít (để nhanh), chậm thì mượt nhiều
        # alpha = self.smooth_factor
        # if dist > 100: alpha = 0.5 # Ví dụ: di chuyển xa thì tăng tốc
        
        self.curr_x += (target_x - self.curr_x) * self.smooth_factor
        self.curr_y += (target_y - self.curr_y) * self.smooth_factor
        
        # Cập nhật vị trí chuột thật
        win32api.SetCursorPos((int(self.curr_x), int(self.curr_y)))

    # --- CÁC HÀM CLICK/SCROLL (GIỮ NGUYÊN) ---
    def click_cursor(self, box, x, y, tol=5):
        x1, x2, y1, y2 = box['x1'], box['x2'], box['y1'], box['y2']
        x_limited = max(x1, min(x, x2))
        y_limited = max(y1, min(y, y2))
        
        # Nếu con trỏ bên ngoài box, đặt cờ và bỏ qua xử lý
        if x <= x1 + tol or x >= x2 - tol or y <= y1 + tol or y >= y2 - tol:
            #print("Out of box, resetting state.")
            self._reset()
            return

        # Kiểm tra có bên trong box hay không
        if x > x1 and x < x2 and y > y1 and y < y2 and self.has_entered_box == False:
            self.has_entered_box = True

        # Nếu chưa từng vào box, không thực hiện thao tác
        if not self.has_entered_box:
            return

        # Xử lý logic click và scroll khi đã vào box
        self._handle_click_logic(x_limited, x1, x2)
        self._handle_scroll_logic(y_limited, y1, y2)

    def _handle_click_logic(self, x_limited, x1, x2, tolerance=5):
        t = time.time()
        left_bound  = x1 + tolerance
        right_bound = x2 - tolerance
        inside_box  = left_bound < x_limited < right_bound
        left_click_prev  = self.left_state
        right_click_prev = self.right_state
        
        if not self.last_box_state and not self.click_state:
            self.last_box_state = inside_box
            return
        
        if not self.click_state and not inside_box:
            self.left_state  = x_limited <= left_bound
            self.right_state = x_limited >= right_bound
            self.click_state = True
            self.click_lasttime = t
            return
        
        if not self.click_state:
            self.last_box_state = inside_box
            return
        
        if inside_box:
            if t - self.click_lasttime >= self.click_delay:
                self.holding = False
                self.click_state = False
                self.click_lasttime = t
                if left_click_prev:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                elif right_click_prev:
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                return
            
            if left_click_prev:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,   0, 0, 0, 0) 
            elif right_click_prev:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,   0, 0, 0, 0) 

            self.click_lasttime = t
            self.click_state = False
        else:
            if t - self.click_lasttime >= self.click_delay and not self.holding:
                self.holding = True
                if left_click_prev:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                elif right_click_prev:
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)

    def _handle_scroll_logic(self, y_limited, y1, y2, tolerance=5):
        inside_box = y1 + tolerance < y_limited < y2 - tolerance
        if not self.last_box_state and not inside_box:        
            return
        elif not self.last_box_state and inside_box:
            self.last_box_state = True
        
        if y_limited <= y1 + tolerance:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, 100, 0)   
        elif y_limited >= y2 - tolerance:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -100, 0)
        
    def _reset(self):
        self.click_state = False
        self.last_box_state = False
        self.left_state = False
        self.right_state = False
        self.holding = False
        self.has_entered_box = False  # Reset trạng thái đã vào box
# ===================================================
# MAIN PROGRAM
# ===================================================
if __name__ == "__main__":
    # 1. Khởi tạo các module
    detector = FootDetector()          # Load model
    controller = CursorController()    # Load config & mouse logic
    
    # 2. Khởi tạo Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # --- Biến đo FPS ---
    prev_time = time.time()
    current_fps = 0.0

    print("System Ready. Press 'q' to exit.")

    while True:
        # --- Đo FPS ---
        current_time = time.time()
        time_diff = current_time - prev_time
        if time_diff > 0:
            current_fps = 1.0 / time_diff
        prev_time = current_time

        # --- Đọc Frame ---
        ret, frame = cap.read()
        if not ret:
            print("Cannot read frame.")
            break
        
        # --- Bước 1: Phát hiện chân (YOLO Inference) ---
        results = detector.detect_foot(frame)
        
        # --- Bước 2: Lấy cấu hình vùng điều khiển mới nhất ---
        click_box = controller.get_limit_box(name="Click_zone")
        move_box = controller.get_limit_box(name="Rec_area")
        
        # --- Bước 3: Xử lý kết quả & Điều khiển chuột ---
        for result in results:
            for box in result.boxes:
                # Lấy tọa độ trung tâm
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                cls_id = int(box.cls[0])
                
                # Class 1: Mốc đỏ (Di chuyển chuột)
                if cls_id == 1: 
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    controller.move_cursor(move_box, cx, cy)
                
                # Class 0: Mốc xanh (Click chuột)
                elif cls_id == 0: 
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                    controller.click_cursor(click_box, cx, cy)
                    
        # --- Bước 4: Vẽ giao diện debug ---
        # Vẽ khung giới hạn Move (Xanh lá)
        cv2.rectangle(frame, (move_box["x1"], move_box["y1"]), (move_box["x2"], move_box["y2"]), (0, 255, 0), 2)
        # Vẽ khung giới hạn Click (Xanh lá)
        cv2.rectangle(frame, (click_box["x1"], click_box["y1"]), (click_box["x2"], click_box["y2"]), (0, 255, 0), 2)
        
        # Vẽ FPS
        fps_text = f"FPS: {current_fps:.2f}"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Foot Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()