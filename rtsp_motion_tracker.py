import cv2
import os
import imutils
import numpy as np
import requests
from datetime import datetime, timedelta

THERMONOTO_CLOUD_BASE_URL = os.environ.get('THERMONOTO_CLOUD_BASE_URL', '')
URL = os.environ.get('WEBCAM_RTSP_URL', '')
SHOW_UI = os.environ.get('SHOW_UI', 'false') == 'true'
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'

def report_movement():
    data = dict(device_id=os.environ.get('HOSTNAME', None))
    print('Posting with', data)
    try:
        response = requests.post(f'{THERMONOTO_CLOUD_BASE_URL}/motion_detection_updates', data=data)
        print(response)
    except Exception:
        return None



# Code adapted from https://github.com/methylDragon/opencv-motion-detector
#

# =============================================================================
# USER-SET PARAMETERS
# =============================================================================

# Number of frames to pass before changing the frame to compare the current
# frame against
FRAMES_TO_PERSIST = 2

# Minimum boxed area for a detected motion to count as actual motion
# Use to filter out noise or small objects
MIN_SIZE_FOR_MOVEMENT = 2000

# Minimum length of time where no motion is detected it should take
#(in program cycles) for the program to declare that there is no movement
MOVEMENT_DETECTED_PERSISTENCE = 2

# Time to rest before capturing another image from the feed
SLEEP_INTERVAL_SECONDS = 5

# =============================================================================
# CORE PROGRAM
# =============================================================================


# Create capture object
cap = cv2.VideoCapture(URL, cv2.CAP_FFMPEG) if URL else cv2.VideoCapture(0)

# Init frame variables
first_frame = None
next_frame = None
last_frame_time = datetime.now()

# Init display font and timeout counters
font = cv2.FONT_HERSHEY_SIMPLEX
delay_counter = 0
movement_persistent_counter = 0


# LOOP!
while True:

    # Set transient motion detected as false
    transient_movement_flag = False
    
    # Read frame
    ret, frame = cap.read()
    text = "Unoccupied"

    # If there's an error in capturing
    if not ret:
        print("CAPTURE ERROR")
        continue

    now_time = datetime.now()
    
    # discard frame if it's under the interval specified.
    if now_time - last_frame_time < timedelta(seconds=SLEEP_INTERVAL_SECONDS):
        continue

    last_frame_time = now_time


    # Resize and save a greyscale version of the image
    frame = imutils.resize(frame, width = 750)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blur it to remove camera noise (reducing false positives)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # If the first frame is nothing, initialise it
    if first_frame is None: first_frame = gray    

    delay_counter += 1

    # Otherwise, set the first frame to compare as the previous frame
    # But only if the counter reaches the appriopriate value
    # The delay is to allow relatively slow motions to be counted as large
    # motions if they're spread out far enough
    if delay_counter > FRAMES_TO_PERSIST:
        delay_counter = 0
        first_frame = next_frame

        
    # Set the next frame to compare (the current frame)
    next_frame = gray

    # Compare the two frames, find the difference
    frame_delta = cv2.absdiff(first_frame, next_frame)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

    # Fill in holes via dilate(), and find contours of the thesholds
    thresh = cv2.dilate(thresh, None, iterations = 2)
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # loop over the contours
    for c in cnts:

        # Save the coordinates of all found contours
        (x, y, w, h) = cv2.boundingRect(c)
        
        # If the contour is too small, ignore it, otherwise, there's transient
        # movement
        if cv2.contourArea(c) > MIN_SIZE_FOR_MOVEMENT:
            transient_movement_flag = True
            
            # Draw a rectangle around big enough movements
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # The moment something moves momentarily, reset the persistent
    # movement timer.
    if transient_movement_flag == True:
        movement_persistent_flag = True
        movement_persistent_counter = MOVEMENT_DETECTED_PERSISTENCE


    # As long as there was a recent transient movement, say a movement
    # was detected    
    if movement_persistent_counter > 0:
        text = "Movement Detected " + str(movement_persistent_counter)
        movement_persistent_counter -= 1
        report_movement()
    else:
        text = "No Movement Detected"

    # Print the text on the screen, and display the raw and processed video 
    # feeds
    if SHOW_UI:
        cv2.putText(frame, str(text), (10,35), font, 0.75, (255,255,255), 2, cv2.LINE_AA)
    else:
        print(str(text))
    
    # For if you want to show the individual video frames
#    cv2.imshow("frame", frame)
#    cv2.imshow("delta", frame_delta)
    
    # Convert the frame_delta to color for splicing
    frame_delta = cv2.cvtColor(frame_delta, cv2.COLOR_GRAY2BGR)

    # Splice the two video frames together to make one long horizontal one
    if SHOW_UI:
        cv2.imshow("frame", np.hstack((frame_delta, frame)))


    # Interrupt trigger by pressing q to quit the open CV program
    ch = cv2.waitKey(1)
    if ch & 0xFF == ord('q'):
        break

# Cleanup when closed
cv2.destroyAllWindows()
cap.release()
