import cv2
import multiprocessing as mp
import time
import module_DETECT_FOOT
import queue
import threading
import module_KEYBOARD
from queue import Empty

VIDEO_CAP = 0
SCALE = 0.7

# =========================================================
# HÀM KHỞI TẠO CAMERA
# =========================================================
def initialize_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # manual exposure
    cap.set(cv2.CAP_PROP_EXPOSURE, -5)      # adjust to your environment
    cap.set(cv2.CAP_PROP_GAIN, 20)          # compensate brightness
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    return cap

# =========================================================
# HÀM XỬ LÝ DỮ LIỆU TỪ QUEUE
# =========================================================
def process_queue(queue, timeout=0.001):
    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None

# =========================================================
# LUỒNG ĐIỀU KHIỂN CHUỘT
# =========================================================
def cursor_worker(cursor_queue, controller, move_box, click_box, stop_event, show_keyboard_event):
    last_x_move, last_y_move = 0, 0
    last_move_box = move_box
    while not stop_event.is_set():
        data = process_queue(cursor_queue)
        if data is None or show_keyboard_event.is_set():
            continue

        action, x, y = data
        if action == "move":
            last_x_move, last_y_move = x, y
            last_move_box = move_box
            controller.move_cursor(move_box, x, y)
        elif action == "click":
            controller.click_cursor(click_box, x, y, -50)
            controller.move_cursor(last_move_box, last_x_move, last_y_move)

# =========================================================
# LUỒNG ĐIỀU KHIỂN BÀN PHÍM
# =========================================================
def keyboard_worker(cursor_queue, keyboard, keyboard_controller, stop_event, show_keyboard_event):
    last_key_pressed = {"move": None, "click": None}
    key_press_time = {"move": None, "click": None}

    while not stop_event.is_set():
        if not show_keyboard_event.is_set():
            time.sleep(0.01)
            continue

        data = process_queue(cursor_queue)
        if data is None:
            continue

        action, x, y = data
        cursor_pos = [x, y]
        key_pressed = keyboard.check_key_collision(cursor_pos)

        if key_pressed:
            if key_pressed != last_key_pressed[action]:
                last_key_pressed[action] = key_pressed
                key_press_time[action] = time.time()
            elif time.time() - key_press_time[action] >= keyboard.delay_click:
                print(f"Thực hiện click phím: {key_pressed}")
                if key_pressed == "CURSOR":
                    show_keyboard_event.clear()
                else:
                    keyboard.handle_key_input(key_pressed, keyboard_controller, keyboard.special_keys)
                last_key_pressed[action] = None
        else:
            last_key_pressed[action] = None

# =========================================================
# HÀM CHÍNH (MAIN PROCESS)
# =========================================================
def main(queue_frame, queue_control):
    cap = initialize_camera()

    detector = module_DETECT_FOOT.FootDetector()
    controller = module_DETECT_FOOT.CursorController()
    keyboard = module_KEYBOARD.VirtualKeyboard(key_size=(45, 45), key_padding=15, key_color=(255, 0, 0), y_offset=50, delay_click=0.8)
    keyboard_controller = module_KEYBOARD.KeyboardController()

    click_box = controller.get_limit_box(name="Click_zone")
    move_box = controller.get_limit_box(name="Rec_area")
    flip_val = False

    show_keyboard_time = time.time()
    show_keyboard_event = threading.Event()
    stop_event = threading.Event()

    cursor_queue = queue.Queue(maxsize=10)

    t_cursor = threading.Thread(
        target=cursor_worker,
        args=(cursor_queue, controller, move_box, click_box, stop_event, show_keyboard_event),
        daemon=True
    )
    t_cursor.start()

    t_keyboard = threading.Thread(
        target=keyboard_worker,
        args=(cursor_queue, keyboard, keyboard_controller, stop_event, show_keyboard_event),
        daemon=True
    )
    t_keyboard.start()

    prev_time = time.time()

    while True:
        current_time = time.time()
        current_fps = 1.0 / (current_time - prev_time) if current_time != prev_time else 0.0
        prev_time = current_time

        ret, frame = cap.read()
        if flip_val:
            frame = cv2.flip(frame, -1)
        if not ret:
            print("Không nhận được frame")
            break

        if not queue_control.empty():
            try:
                control_value = queue_control.get_nowait()
                click_box_dict, move_box_list, flip = control_value
                click_box = click_box_dict
                move_box = {"x1": move_box_list[0], "x2": move_box_list[1], "y1": move_box_list[2], "y2": move_box_list[3]}
                flip_val = flip
            except:
                pass

        results = detector.detect_foot(frame)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                cls_id = int(box.cls[0])

                try:
                    if cursor_queue.full():
                        cursor_queue.get_nowait()

                    if cls_id == 1:  # Mốc đỏ (move)
                        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                        if cx < move_box["x1"] and time.time() - show_keyboard_time > 3:
                            show_keyboard_event.set() if not show_keyboard_event.is_set() else show_keyboard_event.clear()
                            show_keyboard_time = time.time()
                        elif cx >= move_box["x1"]:
                            show_keyboard_time = time.time()
                        cursor_queue.put_nowait(("move", cx, cy))

                    elif cls_id == 0:  # Mốc xanh (click)
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                        cursor_queue.put_nowait(("click", cx, cy))
                except:
                    pass

        if show_keyboard_event.is_set():
            keyboard.draw_keyboard(frame)
        else:
            cv2.rectangle(frame, (move_box["x1"], move_box["y1"]), (move_box["x2"], move_box["y2"]), (0, 0, 255), 2)
            cv2.rectangle(frame, (click_box["x1"], click_box["y1"]), (click_box["x2"], click_box["y2"]), (255, 0, 0), 2)

        fps_text = f"FPS: {current_fps:.2f}"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if queue_frame.full():
            try:
                queue_frame.get_nowait()
            except:
                pass
        queue_frame.put(frame_rgb)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    stop_event.set()
    cap.release()
    cv2.destroyAllWindows()
    t_cursor.join()
    t_keyboard.join()

if __name__ == "__main__":
    mp.set_start_method("spawn")

    queue_frame = mp.Queue(maxsize=3)
    queue_control = mp.Queue(maxsize=3)

    main_process = mp.Process(target=main, args=(queue_frame, queue_control))
    main_process.start()

    try:
        import module_GUI
        import customtkinter as ctk

        root = ctk.CTk()
        app = module_GUI.GUI_frame(root, scale=SCALE, frame_queue=queue_frame, control_queue=queue_control)
        root.mainloop()
    except KeyboardInterrupt:
        pass