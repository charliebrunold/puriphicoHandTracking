import cv2
import mediapipe as mp
import time
import RPi.GPIO as GPIO
import mysql.connector
import threading

db = mysql.connector.connect( # connect to database and input connection details
    host="localhost",
    user="root",
    database=("puriphicoTest")
)
mycursor = db.cursor() # setup cursor

LED_GREEN = 18 # pin calibration
LED_RED = 16
GPIO.setwarnings(False) # GIPO calibration
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_GREEN, GPIO.OUT, initial=GPIO.LOW) 
GPIO.setup(LED_RED, GPIO.OUT, initial=GPIO.HIGH)

cap = cv2.VideoCapture(0) # setup capture device using cv2 library

mpHands = mp.solutions.hands # initalize mediapipe library for hand detection
hands = mpHands.Hands() # declare variable --> used to reference hand library
mpDraw = mp.solutions.drawing_utils # construct drawing framework for user visualization

pTime = 0
cTime = 0 # times responsible for fps calculation 
endTime = 0
startTime = 0 # times responsible for total time calculation
bufferEndTime = 0
bufferStartTime = 0 # times responsible for error buffer
bufferTime = 3 # how long to make the buffer
transactionID = 0 # indexing variable for database log
transactionExpectation = 0 # transaction failsafe in event of misinterpreted data
detection = False # boolean hand detection
firstPass = True # boolean required for buffer timer functionality

def flash(): # flash function to control LED behavior
    GPIO.output(LED_GREEN, GPIO.HIGH)
    GPIO.output(LED_RED, GPIO.HIGH)
    time.sleep(.5)
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)
    time.sleep(.5)
    
try:
    while True:
        success, img = cap.read()
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # show the image in full color
        results = hands.process(imgRGB) # process the image and search for hands
        # print(results.multi_hand_landmarks)
        t = threading.Timer(0, flash) # create threading variable to flash leds 
        
        if results.multi_hand_landmarks: # if results detect multiple hand landmarks in the frame
            localTime = time.ctime(time.time()) # localize time to submit to database transaction
            detection = True # we have detected hands
            if not (firstPass): # if this is not our first pass
                firstPass = True # we need to reset the buffer queue 
            bufferStartTime = 0 # there is no more need for the buffer. make both of these variables 0
            bufferEndTime = 0
            if (transactionID == transactionExpectation): # if our transaction is consistent with what we want to track
                startTime = time.time() # start our timer. this will be used to determine how long we have seen hands in the frame
                transactionExpectation += 1 # we now expect the next transaction, so that there will not be multiple data points for this one handwashing session
            # print(startTime)
            GPIO.output(LED_RED, GPIO.LOW) # indicate detection on LEDs
            
            endTime = time.time()
            if (endTime - startTime >= 20):
                t.start() # start threading process. this will flash LEDs to show detection
                firstPass = False
            
            for handLms in results.multi_hand_landmarks: # for every hand landmark in the frame
                for id, lm in enumerate(handLms.landmark): # for every id of every landmark in the frame
                    # print(id, lm)
                    # h, w, c = img.shape
                    # cx, cy = int(lm.x * w), int(lm.y * h)
                    # print(id, cx, cy)
                    # if id == 8:
                        # cv2.circle(img, (cx, cy), 15, (255, 0 ,255), cv2.FILLED)
                    mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS) # draw the landmarks on the screen in the order they appear

        else: # otherwise, we do not detect hands
            # GPIO.output(LED_RED, GPIO.HIGH)
            # GPIO.output(LED_GREEN, GPIO.LOW)
            if (firstPass): # if this is our first pass through the buffer process, start the buffer time
                bufferStartTime = time.time() # start buffer time. this will count how many seconds have passed without hands on screen
                firstPass = False # no longer consider the first pass significant
            if (detection): # there is detection in the frame
                if (bufferEndTime - bufferStartTime < bufferTime): # if buffer time is under three seconds
                    bufferEndTime = time.time() # update the bufferEndTime
                else: # buffer time has exceeded three seconds. initalize cooldown
                    t.cancel() # stop threading
                    transactionID += 1 # we are new looking for a new transaction
                    endTime = time.time() # set our ending time
                    detection = False # we are no longer detecting hands
                    duration = int(endTime - startTime) # total duration in seconds
                    print(duration) # print this in the console
                    endTime = 0 # our time is now defaulted
                    startTime = 0
                    firstPass = True # it is now our first pass back through
                    mycursor.execute("INSERT INTO handLog3 (time, seconds, buffer) VALUES (%s,%s,%s)", (localTime, duration, bufferTime)) # commit this information to our database
                    db.commit() # finalize
                
        cTime = time.time() # fps counter
        fps = 1/(cTime - pTime) # calculation
        pTime = cTime 

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 3) # display fps in top corner

        cv2.imshow("Image", img) # show image on screen
        cv2.waitKey(1)
except KeyboardInterrupt: # if interrupted
    GPIO.cleanup() # cleanup GIPO board interface