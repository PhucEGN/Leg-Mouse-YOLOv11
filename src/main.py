import cv2
import multiprocessing as mp
import threading
import time

VIDEO_CAP = 0
SCALE = 0.7  # Tỷ lệ phóng to/thu nhỏ giao diện popup GUI

# ============================
# PROCESS: YOLO INFERENCE
# ============================
def yolo_process(frame_queue, result_queue, bbox_queue):
    """
    Nhận frame từ camera (queue), chạy YOLO, trả kết quả qua result_queue
    """
    import module_DETECT_FOOT

    detector = module_DETECT_FOOT.FootDetector()
    
    click_box = detector.get_limit_box(name="Click_zone")
    move_box = detector.get_limit_box(name="Rec_area")
    
    bbox_queue.put([click_box, move_box])
    while True:
        frame = frame_queue.get()
        
        if frame is None:
            continue

        results = detector.detect_foot(frame)
        
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
        
        # trả kết quả
        result_queue.put(annotated_frame)


# ============================
# THREAD: CAMERA CAPTURE
# ============================
def camera_thread(frame_queue, bbox_queue):
    cap = cv2.VideoCapture(VIDEO_CAP, cv2.CAP_DSHOW)
    # Giới hạn độ phân giải khung hình
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("Không mở được camera")
        frame_queue.put(None)
        return

    start = time.time()
    frames = 0
    fps = 0
    
    lim_bbox = bbox_queue.get()
    lim_box_move, lim_box_click = None, None
    while True:
        ret, frame = cap.read()
        if not ret:
            frame_queue.put(None)
            break
        
        frames += 1
        if time.time() - start >= 3:
            print(f"Camera FPS: {fps}")
            start = time.time()
            frames = 0
        
        if lim_bbox is not None and lim_box_move is None:
            lim_box_move = [lim_bbox[0]['x1'], lim_bbox[0]['y1'], lim_bbox[0]['x2'], lim_bbox[0]['y2']]
            lim_box_click = [lim_bbox[1]['x1'], lim_bbox[1]['y1'], lim_bbox[1]['x2'], lim_bbox[1]['y2']]
        else:
            cv2.rectangle(frame, (lim_box_move[0], lim_box_move[1]), (lim_box_move[2], lim_box_move[3]), (0, 255, 0), 2)
            cv2.rectangle(frame, (lim_box_click[0], lim_box_click[1]), (lim_box_click[2], lim_box_click[3]), (0, 255, 0), 2)
        # gửi frame sang YOLO process
        frame_queue.put(frame)
        fps = frames / 3
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            frame_queue.put(None)
            break
        
    cap.release()
    cv2.destroyAllWindows()

# ============================
# MAIN
# ============================
if __name__ == "__main__":
    mp.set_start_method("spawn")  # bắt buộc khi dùng YOLO multiprocessing

    frame_queue = mp.Queue(maxsize=2)    # queue truyền frame sang YOLO
    result_queue = mp.Queue(maxsize=2)   # queue truyền kết quả YOLO về main
    control_queue = mp.Queue(maxsize=1)  # queue điều khiển từ GUI sang YOLO
    bbox_queue = mp.Queue(maxsize=1)     # queue truyền box giới hạn từ YOLO sang Camera
    
    # Khởi động YOLO process
    yolo_p = mp.Process(target=yolo_process, args=(frame_queue, result_queue, bbox_queue))
    yolo_p.start()

    # Khởi động thread camera
    cam_t = mp.Process(target=camera_thread, args=(frame_queue, bbox_queue), daemon=True)
    cam_t.start()

    # MAIN LOOP (UI chạy ở đây)
    try:
        import module_GUI
        import customtkinter as ctk
        
        root = ctk.CTk()
        app = module_GUI.GUI_frame(root, scale=SCALE, frame_queue=frame_queue, control_queue=control_queue)
        root.mainloop()
    except KeyboardInterrupt:
        pass

    # gửi tín hiệu dừng
    frame_queue.put(None)
    result_queue.put(None)

    yolo_p.join()
