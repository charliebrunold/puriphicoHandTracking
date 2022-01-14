import cv2
import mediapipe as mp
import time
import RPi.GPIO as GPIO   

GPIO.setwarnings(False)    
GPIO.setmode(GPIO.BOARD)   
GPIO.setup(23, GPIO.OUT, initial=GPIO.LOW)   # Set pin 23 to be an output pin and set initial value to low (off)
GPIO.setup(24, GPIO.OUT, initial=GPIO.HIGH)   # Set pin 24 to be an output pin and set initial value to HIGH (on)

cap = cv2.VideoCapture(0)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

pTime = 0
cTime = 0

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    # print(results.multi_hand_landmarks)

    if results.multi_hand_landmarks:
        GPIO.output(24, GPIO.LOW) 
        GPIO.output(23, GPIO.HIGH)
        for handLms in results.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                print(id, cx, cy)
                if id == 8:
                    cv2.circle(img, (cx, cy), 15, (255, 0 ,255), cv2.FILLED)

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

    cTime = time.time()
    fps = 1/(cTime - pTime)
    pTime = cTime

    cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 3)

    cv2.imshow("Image", img)
    cv2.waitKey(1)
