import cv2
import numpy as np

class VirtualKeyboard:
    """
    Class đại diện cho Bàn phím Ảo (Virtual Keyboard).
    Chứa các phương thức để định nghĩa và vẽ các phím lên khung hình (frame).
    """
    def __init__(self, key_size=(60, 60), key_padding=5, key_color=(255, 0, 0)):
        """
        Khởi tạo bàn phím.
        :param key_size: Kích thước (chiều rộng, chiều cao) của mỗi phím.
        :param key_padding: Khoảng cách đệm giữa các phím.
        :param key_color: Màu sắc của viền phím (B, G, R).
        """
        self.key_size = key_size
        self.key_padding = key_padding
        self.key_color = key_color
        self.keys = self._define_keys() # Khởi tạo bố cục bàn phím

    def _define_keys(self):
        """
        Định nghĩa bố cục cơ bản của bàn phím QWERTY và trả về danh sách các phím.
        Mỗi phím là một dictionary chứa 'text' (nội dung) và 'pos' (vị trí góc trên bên trái).
        """
        # Bố cục bàn phím đơn giản (chỉ hàng phím đầu tiên - QWERTY)
        # Bạn có thể mở rộng thêm các hàng phím khác
        key_layout = [
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', 
            'CTRL', 'SHIFT', 'SPACE'
        ]

        keys = []
        start_x = self.key_padding # Vị trí X bắt đầu của hàng phím
        start_y = self.key_padding # Vị trí Y bắt đầu của hàng phím
        special_value = 0 # Biến thay đổi kích thước phím đặc biệt
        
        for i, key_text in enumerate(key_layout):
            # Tính toán vị trí góc trên bên trái của phím
            if i >= 10 and i < 19:
                # Hàng phím thứ 2 (A - L)
                special_value = 1
                row = 1
                col = i - 10
                x = start_x + col * (self.key_size[0] + self.key_padding) + (self.key_size[0] // 2)
                y = start_y + row * (self.key_size[1] + self.key_padding)
            elif i >= 19 and i < 26:
                # Hàng phím thứ 3 (Z - M)
                special_value = 1
                row = 2
                col = i - 19
                x = start_x + col * (self.key_size[0] + self.key_padding) + self.key_size[0]
                y = start_y + row * (self.key_size[1] + self.key_padding)
            
            elif key_text == 'CTRL':
                special_value = 2
                x = start_x
                y = start_y + 3 * (self.key_size[1] + self.key_padding)
            
            elif key_text == 'SHIFT':
                special_value = 2
                x = start_x + (self.key_size[0] + self.key_padding) * 2
                y = start_y + 3 * (self.key_size[1] + self.key_padding)
            
            elif key_text == 'SPACE':
                special_value = 2
                x = start_x + (self.key_size[0] + self.key_padding) * 4
                y = start_y + 3 * (self.key_size[1] + self.key_padding)
            
            else:
                # Hàng phím thứ 1 (Q - P)
                special_value = 1
                x = start_x + i * (self.key_size[0] + self.key_padding)
                y = start_y
            
            # Lưu thông tin phím
            keys.append({
                'text': key_text,
                'pos': (x, y), # (x_top_left, y_top_left)
                'bbox': (x, y, x + self.key_size[0] * special_value, y + self.key_size[1]) # (x1, y1, x2, y2)
            })
            
        return keys

    def draw_keyboard(self, frame):
        """
        Vẽ toàn bộ bàn phím lên khung hình video (frame).
        :param frame: Khung hình OpenCV (numpy array) để vẽ lên.
        :return: Khung hình đã được vẽ.
        """
        # 
        for key in self.keys:
            x1, y1, x2, y2 = key['bbox']
            key_text = key['text']

            # 1. Vẽ hình chữ nhật (Khung phím)
            cv2.rectangle(frame, (x1, y1), (x2, y2), self.key_color, 2) # Vẽ viền dày 2

            # 2. Thêm chữ (Nội dung phím)
            # Tính toán vị trí để căn giữa chữ
            if key_text == 'SPACE' or key_text == 'CTRL' or key_text == 'SHIFT':
                text_size = cv2.getTextSize(key_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = x1 + (self.key_size[0] * 2 - text_size[0]) // 2
                text_y = y1 + (self.key_size[1] - text_size[1]) // 2 + text_size[1]
            else:
                text_size = cv2.getTextSize(key_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = x1 + (self.key_size[0] - text_size[0]) // 2
                text_y = y1 + (self.key_size[1] + text_size[1]) // 2
                
            cv2.putText(frame, key_text, (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2) # Chữ màu trắng
            
        return frame

# --- Ví dụ về cách sử dụng ---

if __name__ == '__main__':
    # Khởi tạo đối tượng bàn phím
    keyboard = VirtualKeyboard(key_size=(55, 55), key_padding=8, key_color=(0, 255, 0)) # Màu xanh lá cây

    # Khởi tạo camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # 0 là camera mặc định. Thay bằng 1, 2... nếu cần

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)   # manual exposure
    cap.set(cv2.CAP_PROP_EXPOSURE, -5)       # adjust to your environment
    cap.set(cv2.CAP_PROP_GAIN, 20)           # compensate brightness
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    
    if not cap.isOpened():
        print("Không thể mở camera")
        exit()

    try:
        while True:
            # Đọc khung hình
            ret, frame = cap.read()
            if not ret:
                print("Không nhận được khung hình. Thoát...")
                break
            
            # Lật khung hình theo chiều ngang để dễ thao tác như gương
            frame = cv2.flip(frame, 1)

            # Vẽ bàn phím lên khung hình
            frame_with_keyboard = keyboard.draw_keyboard(frame)
            
            # Hiển thị kết quả
            cv2.imshow('Virtual Keyboard', frame_with_keyboard)

            # Nhấn 'q' để thoát
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Giải phóng tài nguyên
        cap.release()
        cv2.destroyAllWindows()