import cv2
import ultralytics
import win32api
import win32con
import yaml

MODEL_PATH = 'src/asset/model/YOLOv11-215pic.pt'
YAML_CONFIG_PATH = 'src/asset/config/config.yaml'
class FootDetector:
    def __init__(self, model_path=MODEL_PATH):
        # Khởi tạo model YOLO
        self.model = ultralytics.YOLO(model_path)

        # Khởi tạo cursor control
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
    def detect_foot(self, image):
        results = self.model(image)
        return results
   
    def move_cursor(self, x, y):
        win32api.SetCursorPos((x, y))

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

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Phát hiện điểm mốc trong khung hình
        results = detector.detect_foot(frame)
        box = detector.get_limit_box(name="Click_zone")
        
        for result in results:
            annotated_frame = result.plot()
            cv2.imshow('Foot Detection', annotated_frame)
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                # Chuyển đổi tọa độ khung hình sang tọa độ màn hình
                screen_x = int(cx / frame.shape[1] * detector.screen_w)
                screen_y = int(cy / frame.shape[0] * detector.screen_h)
                detector.move_cursor(screen_x, screen_y)
                
                # Chuyển đổi tọa độ khung
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()