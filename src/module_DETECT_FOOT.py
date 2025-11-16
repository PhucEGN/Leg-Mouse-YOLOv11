import cv2
import ultralytics

MODEL_PATH = 'src/asset/model/YOLOv11-215pic.pt'

class FootDetector:
    def __init__(self, model_path=MODEL_PATH):
        self.model = ultralytics.YOLO(model_path)

    def detect_foot(self, image):
        results = self.model(image)
        return results

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
        
        results = detector.detect_foot(frame)
        
        for result in results:
            annotated_frame = result.plot()
            cv2.imshow('Foot Detection', annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()