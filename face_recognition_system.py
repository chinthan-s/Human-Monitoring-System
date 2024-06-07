import cv2
import face_recognition
import sqlite3
import os
import pygame
import smtplib
import email.mime.application
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pyautogui
import queue
import threading
import time
import sys
from datetime import datetime
import tkinter as tk
from PIL import Image, ImageTk
from twilio.rest import Client

# Initialize Pygame for sound playback
pygame.mixer.init()
# Load the alarm sound, ensure you have 'alarm.mp3' in your working directory
alarm_sound = pygame.mixer.Sound('alarm.mp3')

# Initialize the SQLite database and add images to it
class ImageDB:
    def __init__(self, database_path):
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ImageDB 
        (name TEXT, image BLOB)""")
        self.conn.commit()

    def insert_image(self, name, image_data):
        self.cursor.execute("INSERT INTO ImageDB (name, image) VALUES (?, ?)", (name, image_data))
        self.conn.commit()

    def get_all_images(self):
        self.cursor.execute("SELECT * FROM ImageDB")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

# Initialize the face recognition system
class FaceRecognition:
    def __init__(self, database_path, image_directory):
        self.image_db = ImageDB(database_path)
        self.known_face_encodings = []
        self.known_face_names = []
        self.image_directory = image_directory

    def load_known_faces(self):
        data = self.image_db.get_all_images()
        for row in data:
            name, image_data = row
            image_path = os.path.join(self.image_directory, name)
            face_image = face_recognition.load_image_file(image_path)
            face_encoding = face_recognition.face_encodings(face_image)
            if face_encoding:
                self.known_face_encodings.append(face_encoding[0])
                self.known_face_names.append(name)

    def recognize_faces(self, frame):
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            for i, match in enumerate(matches):
                if match:
                    name = self.known_face_names[i]
                    break

            names.append(name)

        return names

# Function to send email and WhatsApp notification in a separate thread

def send_notification_async(email_queue, message_label):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = '   '   # Update with your email address
    sender_password = '   '  # Update with your email password
    recipient_email = '   '  # Update with recipient email address

    # Twilio credentials
    account_sid = '  '  #Update with your Twilio SID number
    auth_token = '   '   #Update with your Twilio token
    client = Client(account_sid, auth_token)
    from_whatsapp_number = 'whatsapp: '#Update with your Twilio number
    to_whatsapp_number = 'whatsapp:+91' #update with your number

    screenshot_folder = 'F:/FACE-RECOGNITION-FINAL/screenshots'  # Update with your screenshot folder path

    while True:
        unknown_person_detected = email_queue.get()

        if unknown_person_detected:
            # Generate a timestamp-based filename for the screenshot
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            screenshot_path = os.path.join(screenshot_folder, f'screenshot_{timestamp}.png')

            # Take a screenshot of the screen when an unknown person is detected
            try:
                screenshot = pyautogui.screenshot()
                screenshot.save(screenshot_path)
            except Exception as e:
                print("Error saving screenshot:", str(e))
                continue

            # Send email with alert and attach the screenshot
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = 'Unknown Person Detected'

            text = MIMEText("An unknown person was detected. Please check the attached screenshot.")
            msg.attach(text)

            with open(screenshot_path, "rb") as attachment:
                part = email.mime.application.MIMEApplication(attachment.read(), _subtype="png")
                part.add_header('Content-Disposition', 'attachment', filename='screenshot.png')
                msg.attach(part)

            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
                server.quit()
                print("Email sent successfully")
                # Notify the GUI that the email is sent
                message_label.config(text="Email sent successfully")
            except Exception as e:
                print("Error sending email:", str(e))
                print("Retrying in 60 seconds...")
                time.sleep(60)  # Introduce a delay before retrying

            # Send WhatsApp message with alert
            message_body = "Unknown person detected! Please check your E-Mail for the image"
            message = client.messages.create(
                body=message_body,
                from_=from_whatsapp_number,
                to=to_whatsapp_number
            )
            print("WhatsApp message sent successfully!")

            # Schedule a function to reset the message label after 3 seconds
            message_label.after(3000, lambda: message_label.config(text=""))



# Main program
def main():
    # Initialize the image database and load known faces
    db = ImageDB("image-dataset/ImageDB.db")  # Update with your image-dataset folder path
    fr = FaceRecognition("image-dataset/ImageDB.db", 'F:/FACE-RECOGNITION-FINAL/Image-dataset')  # Update with your folder path
    fr.load_known_faces()

    # Create a queue to store the emails and WhatsApp messages
    email_queue = queue.Queue()

    # Create a GUI window
    root = tk.Tk()
    root.title("Human Monitoring System For Security Services Using Deep Learning")

    # Load the background image and resize it to match the window's size
    background_image = Image.open("bg1.jpg")  # Replace "background.jpg" with your JPEG image file path
    background_image = background_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS)
    background_photo = ImageTk.PhotoImage(background_image)

    # Create a label to hold the background image
    background_label = tk.Label(root, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1, anchor='nw')

    # Heading label
    heading_label = tk.Label(root, text="Human Monitoring System For Security Services Using Deep Learning", font=("palatino", 28), pady=10, bg="white", fg="black")
    heading_label.pack()

    # Create a frame to hold the canvas (camera feed)
    frame_canvas = tk.Frame(root, bg="white", bd=2, relief=tk.GROOVE)
    frame_canvas.pack()

    # Canvas to display the camera feed
    canvas = tk.Canvas(frame_canvas, width=800, height=600, bg="grey")
    canvas.pack()

    # Label to display messages
    message_label = tk.Label(root, text="", font=("Arial", 14), bg="lightblue", fg="black")
    message_label.pack()

    # Start a thread for sending notifications
    notification_thread = threading.Thread(target=send_notification_async, args=(email_queue, message_label))
    notification_thread.daemon = True  # Daemonize the thread to allow program exit
    notification_thread.start()

    # Open the camera for real-time face detection and recognition
    cam = cv2.VideoCapture(1)

    # Set camera properties for faster processing
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Initialize a flag to track if an unknown person is detected
    unknown_person_detected = False

    # Function to update the camera feed
    def update_frame():
        nonlocal unknown_person_detected

        # Capture a frame from the camera
        ret, frame = cam.read()

        # Resize the frame to match the canvas size
        frame = cv2.resize(frame, (800, 600))  # Adjust size as needed

        # Perform face detection and recognition on every alternate frame
        if update_frame.counter % 2 == 0:
            names = fr.recognize_faces(frame)

            # If an unknown person is detected, play the alarm and send an email with alert
            if "Unknown" in names and not unknown_person_detected:
                alarm_sound.play(-1)  # Play the alarm sound indefinitely
                unknown_person_detected = True
                email_queue.put(True)
                message_label.config(text="Unknown person detected", bg="red", fg="white")

            # If a known person is detected, stop the alarm
            elif "Unknown" not in names and unknown_person_detected:
                alarm_sound.stop()
                unknown_person_detected = False
                message_label.config(text="Known Person detected", bg="green", fg="white")

        else:
            # If not processing the frame, set names to an empty list
            names = []

        update_frame.counter += 1

        # Display recognized faces on the camera feed
        for (top, right, bottom, left), name in zip(face_recognition.face_locations(frame), names):
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            font = cv2.FONT_HERSHEY_DUPLEX

            # Extract the name without the file extension
            name_without_extension = os.path.splitext(name)[0]

            cv2.putText(frame, name_without_extension, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

        # Display the date and time on the camera feed
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Convert the frame from OpenCV format to Pillow format
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = ImageTk.PhotoImage(image=img)

        # Update the canvas with the new image
        canvas.create_image(0, 0, anchor=tk.NW, image=img)
        canvas.img = img

        # Schedule the next update
        root.after(30, update_frame)

    # Initialize update_frame counter
    update_frame.counter = 0


    # Start updating the camera feed
    update_frame()

    def on_closing():
        # Release the camera and close any windows
        cam.release()
        cv2.destroyAllWindows()
        db.close()
        root.destroy()
        # Exit the program gracefully
        sys.exit()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Run the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
