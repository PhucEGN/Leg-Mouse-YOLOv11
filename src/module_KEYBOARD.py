from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
import time
import cv2
import numpy as np

class VirtualKeyboard:
    """
    Class đại diện cho Bàn phím Ảo (Virtual Keyboard).
    Chứa các phương thức để định nghĩa và vẽ các phím lên khung hình (frame).
    """
    def __init__(self, key_size=(60, 60), key_padding=5, key_color=(255, 0, 0), y_offset=0, delay_click=2):
        """
        Khởi tạo bàn phím.
        :param key_size: Kích thước (chiều rộng, chiều cao) của mỗi phím.
        :param key_padding: Khoảng cách đệm giữa các phím.
        :param key_color: Màu sắc của viền phím (B, G, R).
        :param y_offset: Giá trị dịch chuyển theo trục Y cho toàn bộ bàn phím.
        """
        self.key_size = key_size
        self.key_padding = key_padding
        self.key_color = key_color
        self.y_offset = y_offset
        self.keys = self._define_keys() # Khởi tạo bố cục bàn phím
        self.key_states = {key['text']: False for key in self.keys}  # Trạng thái của các phím (True nếu đang giữ)
        self.delay_click = delay_click  # Thời gian chờ (giây) trước khi thực hiện nhấn phím
        self.special_keys = {
            'SPACE': ' ',
            'CTRL': Key.ctrl,
            'SHIFT': Key.shift,
            'BACKSPACE': Key.backspace
        }
        
    def _define_keys(self):
        """
        Định nghĩa bố cục cơ bản của bàn phím QWERTY và trả về danh sách các phím.
        Mỗi phím là một dictionary chứa 'text' (nội dung) và 'pos' (vị trí góc trên bên trái).
        """
        # Bố cục bàn phím đơn giản (chỉ hàng phím đầu tiên - QWERTY)
        # Bạn có thể mở rộng thêm các hàng phím khác
        key_layout = [
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l',
            'z', 'x', 'c', 'v', 'b', 'n', 'm',
            'CTRL', 'SHIFT', 'SPACE', 'BACKSPACE'
        ]

        keys = []
        start_x = self.key_padding # Vị trí X bắt đầu của hàng phím
        start_y = self.key_padding + self.y_offset # Vị trí Y bắt đầu của hàng phím (cộng thêm y_offset)
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
            
            elif key_text == 'BACKSPACE':
                special_value = 2
                x = start_x + (self.key_size[0] + self.key_padding) * 6
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
        for key in self.keys:
            x1, y1, x2, y2 = key['bbox']
            key_text = key['text']

            # Thay đổi màu viền nếu phím đang được giữ
            color = (0, 255, 255) if self.key_states.get(key_text, False) else self.key_color

            # Vẽ hình chữ nhật (Khung phím)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Tính toán vị trí chữ và vẽ chữ
            text_size = cv2.getTextSize(key_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = x1 + (self.key_size[0] * (2 if key_text in ['SPACE', 'CTRL', 'SHIFT', 'BACKSPACE'] else 1) - text_size[0]) // 2
            text_y = y1 + (self.key_size[1] - text_size[1]) // 2 + text_size[1]
            cv2.putText(frame, key_text.upper(), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def check_key_collision(self, cursor_pos):
        """
        Kiểm tra xem con trỏ có nằm trong vùng của một phím không.
        :param cursor_pos: Vị trí của con trỏ (x, y).
        :return: Giá trị của phím nếu có va chạm, ngược lại trả về None.
        """
        cursor_x, cursor_y = cursor_pos
        for key in self.keys:
            x1, y1, x2, y2 = key['bbox']
            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                return key['text']
        return None

    def toggle_key_state(self, key_text):
        """
        Chuyển đổi trạng thái giữ (hold) của phím.
        :param key_text: Nội dung của phím.
        """
        if key_text in self.key_states:
            self.key_states[key_text] = not self.key_states[key_text]

    def handle_key_input(self, key_text, keyboard_controller, special_keys):
        """
        Xử lý nhập liệu cho phím được nhấn.
        :param key_text: Nội dung của phím được nhấn.
        :param keyboard_controller: Đối tượng điều khiển bàn phím.
        :param special_keys: Từ điển ánh xạ các phím đặc biệt.
        """
        if key_text in special_keys:  # Xử lý các phím đặc biệt
            if key_text in ['CTRL', 'SHIFT']:
                self.toggle_key_state(key_text)  # Chuyển đổi trạng thái giữ
                if self.key_states[key_text]:
                    keyboard_controller.press(special_keys[key_text])
                else:
                    keyboard_controller.release(special_keys[key_text])
            else:
                keyboard_controller.press(special_keys[key_text])
                keyboard_controller.release(special_keys[key_text])
        else:  # Xử lý các phím thông thường
            keyboard_controller.press(key_text)
            keyboard_controller.release(key_text)

class CursorController:
    """
    Lớp điều khiển con trỏ trên camera.
    """
    def __init__(self, frame_width, frame_height, cursor_color=(0, 0, 255), cursor_size=10):
        """
        Khởi tạo con trỏ.
        :param frame_width: Chiều rộng của khung hình.
        :param frame_height: Chiều cao của khung hình.
        :param cursor_color: Màu sắc của con trỏ (B, G, R).
        :param cursor_size: Kích thước của con trỏ.
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.cursor_color = cursor_color
        self.cursor_size = cursor_size
        self.cursor_pos = [frame_width // 2, frame_height // 2]  # Vị trí ban đầu ở giữa khung hình
        
    def move_cursor(self, direction):
        """
        Di chuyển con trỏ theo hướng chỉ định.
        :param direction: Hướng di chuyển ('up', 'down', 'left', 'right').
        """
        step = 10  # Khoảng cách di chuyển mỗi lần nhấn phím
        if direction == 'up':
            self.cursor_pos[1] = max(0, self.cursor_pos[1] - step)
        elif direction == 'down':
            self.cursor_pos[1] = min(self.frame_height, self.cursor_pos[1] + step)
        elif direction == 'left':
            self.cursor_pos[0] = max(0, self.cursor_pos[0] - step)
        elif direction == 'right':
            self.cursor_pos[0] = min(self.frame_width, self.cursor_pos[0] + step)

    def draw_cursor(self, frame):
        """
        Vẽ con trỏ lên khung hình.
        :param frame: Khung hình OpenCV (numpy array) để vẽ lên.
        :return: Khung hình đã được vẽ.
        """
        x, y = self.cursor_pos
        cv2.circle(frame, (x, y), self.cursor_size, self.cursor_color, -1)  # Vẽ con trỏ hình tròn
        return frame

# --- Ví dụ về cách sử dụng ---

if __name__ == '__main__':
    # Khởi tạo đối tượng bàn phím
    keyboard = VirtualKeyboard(key_size=(55, 55), key_padding=8, key_color=(0, 255, 0), y_offset=100) # Màu xanh lá cây

    # Khởi tạo hai con trỏ
    cursor1 = CursorController(frame_width=640, frame_height=480, cursor_color=(0, 0, 255))  # Con trỏ 1 (màu đỏ)
    cursor2 = CursorController(frame_width=640, frame_height=480, cursor_color=(0, 255, 0))  # Con trỏ 2 (màu xanh lá)

    # Khởi tạo đối tượng điều khiển chuột và bàn phím
    mouse = Controller()
    keyboard_controller = KeyboardController()

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

    # Ánh xạ các phím đặc biệt sang mã phím của pynput

    try:
        prev_time = cv2.getTickCount()  # Thời gian bắt đầu
        last_key_pressed = None
        key_press_time = None

        while True:
            # Đọc khung hình
            ret, frame = cap.read()
            if not ret:
                print("Không nhận được khung hình. Thoát...")
                break

            # Lật khung hình và vẽ bàn phím, con trỏ
            frame = cv2.flip(frame, 1)
            frame = cursor2.draw_cursor(cursor1.draw_cursor(keyboard.draw_keyboard(frame)))

            # Kiểm tra va chạm của con trỏ 1 với các phím
            key_pressed = keyboard.check_key_collision(cursor1.cursor_pos)
            if key_pressed:
                if key_pressed != last_key_pressed:
                    last_key_pressed = key_pressed
                    key_press_time = time.time()
                elif time.time() - key_press_time >= keyboard.delay_click:  # Chờ thời gian delay
                    print(f"Thực hiện click phím: {key_pressed}")
                    keyboard.handle_key_input(key_pressed, keyboard_controller, keyboard.special_keys)
                    last_key_pressed = None
            else:
                last_key_pressed = None

            # Tính toán FPS và hiển thị
            current_time = cv2.getTickCount()
            fps = cv2.getTickFrequency() / (current_time - prev_time)
            prev_time = current_time
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Hiển thị kết quả
            cv2.imshow('Virtual Keyboard', frame)

            # Xử lý sự kiện phím nhấn
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key in [ord('w'), ord('W')]:
                cursor1.move_cursor('up')
            elif key in [ord('s'), ord('S')]:
                cursor1.move_cursor('down')
            elif key in [ord('a'), ord('A')]:
                cursor1.move_cursor('left')
            elif key in [ord('d'), ord('D')]:
                cursor1.move_cursor('right')
            elif key in [ord('i'), ord('I')]:
                cursor2.move_cursor('up')
            elif key in [ord('k'), ord('K')]:
                cursor2.move_cursor('down')
            elif key in [ord('j'), ord('J')]:
                cursor2.move_cursor('left')
            elif key in [ord('l'), ord('L')]:
                cursor2.move_cursor('right')

    finally:
        cap.release()
        cv2.destroyAllWindows()