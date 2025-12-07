import cv2
import ultralytics
import win32api
import win32con
import yaml
import time

MODEL_PATH = 'src/asset/model/YOLOv11-215pic.pt'
YAML_CONFIG_PATH = 'src/asset/config/config.yaml'
class FootDetector:
    def __init__(self, model_path=MODEL_PATH):
        # Khởi tạo model YOLO
        self.model = ultralytics.YOLO(model_path)

        # Khởi tạo cursor control
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
        # Value
        self.click_state = False # Nếu chuột ở bên trong box sẽ True
        self.last_box_state = False # Lưu trạng thái click trước đó
        self.left_state = False
        self.right_state = False
        self.holding = False # Giữ trạng thái click
        
        self.click_delay = 0.5   # Thời gian delay giữa các lần click (nếu cần)
        self.click_lasttime = 0.0
        
    def detect_foot(self, image):
        results = self.model(image, verbose=False)
        return results
   
    def _move_cursor(self, x, y):
        win32api.SetCursorPos((x, y))

    def move_cursor(self, box, x, y):
        """Di chuyển con trỏ đến vị trí x, y (giới hạn trong limit box)

        Args:
            box (dict): A dictionary containing the coordinates of the limit box.
            x (int): Tọa độ x của điểm mốc trên khung hình
            y (int): Tọa độ y của điểm mốc trên khung hình
        Returns:
            None
        """
        x1, x2, y1, y2 = box['x1'], box['x2'], box['y1'], box['y2']
        
        # 1. Giới hạn tọa độ trong vùng box trên frame
        x_limited = max(x1, min(x, x2))
        y_limited = max(y1, min(y, y2))
        
        if x_limited <= x1 or x_limited >= x2 or y_limited <= y1 or y_limited >= y2:
            return
        
        # Kích thước của limit box trên frame
        box_width = x2 - x1
        box_height = y2 - y1
        
        if box_width == 0 or box_height == 0:
            # Xử lý trường hợp box rỗng hoặc có chiều rộng/cao bằng 0
            return 

        # 2. Tính Tỷ lệ Tương đối của (x, y) bên trong limit box (0 đến 1)
        # Bắt đầu từ tọa độ (x1, y1) của box
        relative_x = (x_limited - x1) / box_width
        relative_y = (y_limited - y1) / box_height

        # 3. Chuyển đổi Tỷ lệ Tương đối này sang Tọa độ Màn hình (scale toàn màn hình)
        # Tọa độ màn hình sẽ là Tỷ lệ * Kích thước màn hình
        screen_x = int(relative_x * self.screen_w)
        screen_y = int(relative_y * self.screen_h)
    
        self._move_cursor(screen_x, screen_y)
    
    def click_cursor(self, box, x, y):
        """Thực hiện thao tác click chuột trái, phải và thao tác cuộn chuột.

        Args:
            box (dict): A dictionary containing the coordinates of the limit box.
            x (int): Tọa độ x của điểm mốc trên khung hình
            y (int): Tọa độ y của điểm mốc trên khung hình
        Returns:
            None
        """
        x1, x2, y1, y2 = box['x1'], box['x2'], box['y1'], box['y2']
        
        # 1. Giới hạn tọa độ trong vùng box trên frame
        x_limited = max(x1, min(x, x2))
        y_limited = max(y1, min(y, y2))
        
        self._left_right_click(x_limited, x1, x2)
        self._scroll_cursor(y_limited, y1, y2)
        
    def _left_right_click(self, x_limited, x1, x2, tolerance=5):
        """ Thực hiện thao tác click chuột trái/phải
        
        Args:
            x_limited (int): Tọa độ x đã được giới hạn trong box.
            x1 (int): Tọa độ x1 của box.
            x2 (int): Tọa độ x2 của box.
            tolerance (int, optional): Độ dung sai để xác định vùng click. Mặc định là 5.
        """
        t = time.time()

        left_bound  = x1 + tolerance
        right_bound = x2 - tolerance
        inside_box  = left_bound < x_limited < right_bound

        left_click_prev  = self.left_state
        right_click_prev = self.right_state
        
        # 0. Kiểm tra đã ở trong box hay chưa, trước khi xử lý tiếp tục
        if not self.last_box_state and not self.click_state:
            self.last_box_state = inside_box
            return
        
        # 1. Nếu điểm mốc vẫn còn ngoài box -> lưu trạng thái click
        if not self.click_state and not inside_box:
            # lưu trạng thái click tại thời điểm vào box
            self.left_state  = x_limited <= left_bound
            self.right_state = x_limited >= right_bound
            
            self.click_state = True
            self.click_lasttime = t
            return
        
        if not self.click_state:
            self.last_box_state = inside_box
            return
        
        # 2. Nếu điểm mốc vẫn còn trong box -> thực hiện click
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
            
        #. 3. Nếu điểm mốc rời khỏi box (giữ thời gian đủ lâu) -> giữ click
        else:
            if t - self.click_lasttime >= self.click_delay and self.holding == False:
                self.holding = True
                if left_click_prev:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                elif right_click_prev:
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
      
    def _scroll_cursor(self, y_limited, y1, y2, tolerance=5):
        """ Thực hiện thao tác cuộn chột
        
        Args:
            y_limited (dict): Giới hạn tọa độ trục y
            x1 (int): Tọa độ x của điểm mốc trên khung hình
            y2 (int): Tọa độ y của điểm mốc trên khung hình
        Returns:
            None
        """
        inside_box = y1 + tolerance < y_limited < y2 - tolerance
        
        # 1. Kiểm tra đã ở trong box hay chưa, trước khi xử lý tiếp tục
        if not self.last_box_state and not inside_box:        
            return
        elif not self.last_box_state and inside_box:
            self.last_box_state = True
            
        # 2. Thực hiện cuộn chuột
        if y_limited <= y1 + tolerance:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, 100, 0)  # Cuộn lên
        elif y_limited >= y2 - tolerance:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -100, 0)   # Cuộn xuống
            
    # Read YAML config file
    def _read_config(self, config_path):
        """Đọc file YAML

        Args:
            config_path (str): Đường dẫn tới file cấu hình YAML.

        Returns:
            dict: Nội dung của file YAML dưới dạng dictionary.
        """
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    # Get Limit Box from config
    def get_limit_box(self, config_path=YAML_CONFIG_PATH, name="Click_zone"):
        """Get the limit box coordinates from the YAML configuration file.

        Args:
            config_path (str, optional): Path to the YAML config file. Defaults to YAML_CONFIG_PATH.
            name (str, optional): The name of the box section in the config. Defaults to "Click_zone".
        Returns:
            dict: A dictionary containing the coordinates of the limit box.
        """
        config = self._read_config(config_path)
        box = config.get(name, {})
        x1, x2, y1, y2 = box.get('x1', 0), box.get('x2', 0), box.get('y1', 0), box.get('y2', 0)
        diction = {"x1": x1, "x2": x2, "y1": y1, "y2": y2}
        return diction
    
if __name__ == "__main__":
    detector = FootDetector()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    # Giới hạn độ phân giải khung hình
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Phát hiện điểm mốc trong khung hình
        results = detector.detect_foot(frame)
        
        click_box = detector.get_limit_box(name="Click_zone")
        move_box = detector.get_limit_box(name="Rec_area")
        
        for result in results:
            annotated_frame = result.plot()
            for box in result.boxes:
                if box.cls[0] == 1: # '1' là mốc đỏ
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    cv2.circle(annotated_frame, (cx, cy), 5, (0, 0, 255), -1)
                    detector.move_cursor(move_box, cx, cy)
                
                if box.cls[0] == 0: # '0' là mốc xanh
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    cv2.circle(annotated_frame, (cx, cy), 5, (255, 0, 0), -1)
                    detector.click_cursor(click_box, cx, cy)
                    
                # Chuyển đổi tọa độ khung
        cv2.rectangle(annotated_frame, (move_box["x1"], move_box["y1"]), (move_box["x2"], move_box["y2"]), (0, 255, 0), 2)
        cv2.rectangle(annotated_frame, (click_box["x1"], click_box["y1"]), (click_box["x2"], click_box["y2"]), (0, 255, 0), 2)
        
        cv2.imshow('Foot Detection', annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()