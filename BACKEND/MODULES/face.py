import cv2
import numpy as np
import time
from tensorflow.keras.models import load_model

# Load model
model = load_model('backend/models/emotion_model.hdf5', compile=False)

# Load face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Emotion labels
emotions = ['Angry','Disgust','Fear','Happy','Sad','Surprise','Neutral']

# Store last predictions (for smoothing)
emotion_history = []

# Convert emotion to score
def emotion_to_score(emotion):
    mapping = {
        "Happy": 0,
        "Neutral": 1,
        "Surprise": 1,
        "Sad": 2,
        "Disgust": 2,
        "Angry": 3,
        "Fear": 3
    }
    return mapping.get(emotion, 1)


def get_emotion_output(prediction):
    confidence = float(np.max(prediction))
    emotion = emotions[np.argmax(prediction)]

    # Apply confidence threshold
    if confidence < 0.5:
        emotion = "Uncertain"

    score = emotion_to_score(emotion)

    return {
        "emotion": emotion,
        "confidence": confidence,
        "score": score
    }


# 🔥 MAIN BACKEND FUNCTION
def detect_emotion(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    results = []

    if len(faces) > 0:
        # Take largest face only
        faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
        (x, y, w, h) = faces[0]

        face = gray[y:y+h, x:x+w]

        # Improve contrast
        face = cv2.equalizeHist(face)

        # preprocess
        face = cv2.resize(face, (64,64))
        face = face / 255.0
        face = np.reshape(face, (1,64,64,1))

        prediction = model.predict(face, verbose=0)

        result = get_emotion_output(prediction)

        # 🔥 Smoothing (last 10 frames)
        emotion_history.append(result["emotion"])
        if len(emotion_history) > 10:
            emotion_history.pop(0)

        # Most frequent emotion
        final_emotion = max(set(emotion_history), key=emotion_history.count)
        result["emotion"] = final_emotion
        result["score"] = emotion_to_score(final_emotion)

        result["box"] = [int(x), int(y), int(w), int(h)]

        results.append(result)

    return results


# 🔧 MAIN RUN FUNCTION WITH 30s TRACKING
def run_emotion_detection():
    cap = cv2.VideoCapture(0)

    start_time = time.time()
    session_duration = 30  # seconds

    session_scores = []
    session_emotions = []

    print("Recording for 30 seconds...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera not working")
            break

        results = detect_emotion(frame)

        for res in results:
            x, y, w, h = res["box"]
            emotion = res["emotion"]
            score = res["score"]
            confidence = res["confidence"]

            # 🔥 Store results
            session_scores.append(score)
            session_emotions.append(emotion)

            text = f"{emotion} ({score}) [{confidence:.2f}]"

            cv2.putText(frame, text, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

            cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)

        # ⏱️ Show timer on screen
        remaining = int(session_duration - (time.time() - start_time))
        cv2.putText(frame, f"Time Left: {remaining}s", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        cv2.imshow("Emotion Detection (30s Session)", frame)

        # Stop after 30 seconds
        if time.time() - start_time > session_duration:
            break

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    # 🔥 FINAL RESULT
    if session_scores:
        avg_score = sum(session_scores) / len(session_scores)
        final_emotion = max(set(session_emotions), key=session_emotions.count)

        print("\n===== FINAL RESULT (30s) =====")
        print(f"Final Emotion  : {final_emotion}")
        print(f"Average Score  : {avg_score:.2f}")
        print(f"Frames Analyzed: {len(session_scores)}")
    else:
        print("\nNo face detected during session.")


# 🚀 RUN
if __name__ == "__main__":
    run_emotion_detection()