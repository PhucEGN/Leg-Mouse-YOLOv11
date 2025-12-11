import cv2
import multiprocessing as mp
import time
import module_DETECT_FOOT # Import module chứa 2 class đã tách
import queue
import threading

VIDEO_CAP = 0
SCALE = 0.7

FRAME = None

# =========================================================
# HÀM CHẠY TRONG LUỒNG RIÊNG: ĐIỀU KHIỂN CON TRỎ
# =========================================================
def cursor_worker(cursor_queue, controller, move_box, click_box, stop_event):
    """
    Luồng riêng chỉ để di chuyển chuột, tránh làm block luồng camera.
    """
    while not stop_event.is_set():
        try:
            # Lấy dữ liệu từ queue, chờ tối đa 0.001s để không chiếm CPU
            # data format: ("action_type", x, y)
            data = cursor_queue.get(timeout=0.001)
            
            action, x, y = data
            
            if action == "move":
                controller.move_cursor(move_box, x, y)
            elif action == "click":
                controller.click_cursor(click_box, x, y, -50)
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Cursor Thread Error: {e}")
            
# =========================================================
# HÀM CHÍNH (MAIN PROCESS)
# =========================================================
def main(queue_frame, queue_control):
    # --- 1. KHỞI TẠO CAMERA ---
    # global FRAME # Không cần thiết nếu bạn không dùng FRAME toàn cục
    # Giả định VIDEO_CAP = 0
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # Giới hạn độ phân giải khung hình
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # --- 2. KHỞI TẠO DETECTOR VÀ CONTROLLER ---
    detector = module_DETECT_FOOT.FootDetector()
    controller = module_DETECT_FOOT.CursorController()
    
    # Lấy cấu hình vùng giới hạn ban đầu
    click_box = controller.get_limit_box(name="Click_zone")
    move_box = controller.get_limit_box(name="Rec_area")
    flip_val = False
    # --- 3. KHỞI TẠO LUỒNG ĐIỀU KHIỂN CHUỘT (CURSOR THREAD) ---
    # Queue nội bộ để truyền dữ liệu từ YOLO -> Cursor Thread
    # maxsize=5 để tránh delay nếu xử lý không kịp (drop frame cũ)
    cursor_queue = queue.Queue(maxsize=10) 
    stop_event = threading.Event()
    
    t_cursor = threading.Thread(
        target=cursor_worker, 
        args=(cursor_queue, controller, move_box, click_box, stop_event),
        daemon=True
    )
    t_cursor.start()
    
    # --- 4. BIẾN ĐO FPS ---
    prev_time = time.time()
    current_fps = 0.0
    
    # =========================================================
    # VÒNG LẶP CHÍNH
    # =========================================================
    while True:
        # --- BẮT ĐẦU LOGIC ĐO FPS ---
        current_time = time.time()
        time_diff = current_time - prev_time
        
        # Tính FPS: 1 / thời gian trôi qua
        if time_diff > 0:
            current_fps = 1.0 / time_diff
        
        prev_time = current_time 
        # --- KẾT THÚC LOGIC ĐO FPS ---

        ret, frame = cap.read()
        if flip_val:
            frame = cv2.flip(frame, -1) # Mirror image

        if not ret:
            print("không nhận được frame")
            break
        
        # --- CẬP NHẬT CẤU HÌNH TỪ GUI (NẾU CÓ) ---
        # Nếu GUI gửi thay đổi vùng box qua queue_control, cập nhật tại đây
        # (Đoạn này tùy chọn, nếu bạn muốn chỉnh vùng realtime)
        if not queue_control.empty():
            try:
                # Giả sử GUI gửi signal cập nhật, ta load lại từ file hoặc từ queue
                # Ở đây demo đơn giản là load lại từ file
                control_value = queue_control.get_nowait() # Clear queue item
                
                click_box_dict, move_box_list, flip = control_value
                #print("Cập nhật vùng giới hạn từ GUI...", click_box, move_box)
                
                click_box = click_box_dict
                move_box = {"x1": move_box_list[0],
                            "x2": move_box_list[1],
                            "y1": move_box_list[2],
                            "y2": move_box_list[3]}
                flip_val = flip
            except: pass

        # ------------------------------------ YOLO Process
        # Phát hiện điểm mốc trong khung hình
        results = detector.detect_foot(frame)
        
        for result in results:
            for box in result.boxes:
                # Lấy tọa độ
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                cls_id = int(box.cls[0])
                
                if cls_id == 1: # '1' là mốc đỏ (move)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    
                    # [THAY ĐỔI] Thay vì gọi trực tiếp, ta đẩy vào Queue cho Thread xử lý
                    try:
                        # put_nowait: Nếu queue đầy thì bỏ qua frame này để tránh lag
                        if cursor_queue.full():
                            cursor_queue.get_nowait()
                        cursor_queue.put_nowait(("move", cx, cy))
                    except: pass
                
                elif cls_id == 0: # '0' là mốc xanh (click)
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                    
                    # [THAY ĐỔI] Đẩy vào Queue
                    try:
                        if cursor_queue.full():
                            cursor_queue.get_nowait()
                        cursor_queue.put_nowait(("click", cx, cy))
                    except: pass
                    
        # Chuyển đổi tọa độ khung để vẽ debug
        cv2.rectangle(frame, (move_box["x1"], move_box["y1"]), (move_box["x2"], move_box["y2"]), (0, 0, 255), 2)
        cv2.rectangle(frame, (click_box["x1"], click_box["y1"]), (click_box["x2"], click_box["y2"]), (255, 0, 0), 2)
        
        # draw tol
        """
        cv2.rectangle(
            frame, 
            (click_box["x1"] + -50, click_box["y1"] + -50), 
            (click_box["x2"] - -50, click_box["y2"] - -50), 
            (255, 255, 0), 
            1
        )
        """
        # ------------------------------------
        
        # --- HIỂN THỊ FPS LÊN KHUNG HÌNH ---
        fps_text = f"FPS: {current_fps:.2f}"
        cv2.putText(
            frame, 
            fps_text, 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0), 
            2 
        )
        # -----------------------------------
        
        # Chuyển màu và gửi sang GUI
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Kiểm tra queue frame đầy chưa để tránh delay GUI
        if queue_frame.full():
            try: queue_frame.get_nowait()
            except: pass
        queue_frame.put(frame_rgb)
        
        # (Tùy chọn) Hiển thị cửa sổ debug riêng nếu cần
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set() # Báo hiệu dừng thread cursor
            break

    # Dọn dẹp
    stop_event.set()
    cap.release()
    cv2.destroyAllWindows()
    t_cursor.join() # Chờ thread kết thúc
            
if __name__ == "__main__":
    mp.set_start_method("spawn")
    
    queue_frame = mp.Queue(maxsize=3)
    queue_control = mp.Queue(maxsize=3)
    
    main_process = mp.Process(target=main, args=(
        queue_frame, queue_control
    ))
    main_process.start()
    
    # MAIN LOOP (UI chạy ở đây)
    try:
        import module_GUI
        import customtkinter as ctk
        
        root = ctk.CTk()
        app = module_GUI.GUI_frame(root, scale=SCALE, frame_queue=queue_frame, control_queue=queue_control)
        root.mainloop()
    except KeyboardInterrupt:
        pass