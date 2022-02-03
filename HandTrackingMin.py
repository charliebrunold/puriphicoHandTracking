import cv2
import mediapipe as mp
import time
import RPi.GPIO as GPIO
import mysql.connector
import threading

db = mysql.connector.connect(
    host="localhost",
    user="pi",
    passwd="puriphicotest",
    database=("puriphicoTest")
)
mycursor = db.cursor()

LED_GREEN = 18
LED_RED = 16
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_GREEN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LED_RED, GPIO.OUT, initial=GPIO.HIGH)

cap = cv2.VideoCapture(0)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

pTime = 0
cTime = 0

localTime = time.ctime(time.time())
detection = False

def flash():
    GPIO.output(LED_GREEN, GPIO.HIGH)
    time.sleep(.5)
    GPIO.output(LED_GREEN, GPIO.LOW)
    time.sleep(.5)
    

try:
    while True:
        success, img = cap.read()
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        # print(results.multi_hand_landmarks)

        if results.multi_hand_landmarks:
            detection = True
            startTime = time.time()
            GPIO.output(LED_RED, GPIO.LOW)
            t = threading.Timer(0, flash)
            t.start()
            
            for handLms in results.multi_hand_landmarks:
                # for id, lm in enumerate(handLms.landmark):
                    # print(id, lm)
                    # h, w, c = img.shape
                    # cx, cy = int(lm.x * w), int(lm.y * h)
                    # print(id, cx, cy)
                    # if id == 8:
                        # cv2.circle(img, (cx, cy), 15, (255, 0 ,255), cv2.FILLED)

                mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
        else:
            t.cancel()
            GPIO.output(LED_RED, GPIO.HIGH)
            GPIO.output(LED_GREEN, GPIO.LOW)
            endTime = time.time()
            if (detection):
                detection = False
                duration = (int) endTime - startTime
                endTime = 0
                startTime = 0
                mycursor.execute("INSERT INTO handLog2 (time, seconds) VALUES (%s,%s)", (localTime, duration))
                db.commit()
                
        cTime = time.time()
        fps = 1/(cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 3)

        cv2.imshow("Image", img)
        cv2.waitKey(1)
except KeyboardInterrupt: 
    GPIO.cleanup()

