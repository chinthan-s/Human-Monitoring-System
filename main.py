import sqlite3
import os

class Image(object):

    def __init__(self):
        self.image_name = []

    def load_directory(self, path='F:/FACE-RECOGNITION-FINAL/Image-dataset'):  # Update with your image-dataset folder path
        for x in os.listdir(path):
            self.image_name.append(x)
        return self.image_name

    def create_database(self, name, image):
        conn = sqlite3.connect("ImageDB.db")
        cursor = conn.cursor()

        # Create the table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ImageDB 
        (name TEXT, image BLOB)""")

        # Check if an image with the same name already exists in the database
        cursor.execute("SELECT COUNT(*) FROM ImageDB WHERE name = ?", (name,))
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("""INSERT INTO ImageDB (name, image) VALUES (?, ?)""", (name, image))

        conn.commit()
        cursor.close()
        conn.close()


def main():
    obj = Image()
    os.chdir('F:/FACE-RECOGNITION-FINAL/Image-dataset')    # Update with your image-dataset folder path

    # Create the table first before adding images
    conn = sqlite3.connect("ImageDB.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ImageDB 
    (name TEXT, image BLOB)""")
    conn.commit()
    conn.close()

    for x in obj.load_directory():
        if ".png" in x or ".jpg" in x:
            with open(x, "rb") as f:
                data = f.read()
                obj.create_database(name=x, image=data)
                print("{} added to database".format(x))

def fetch_data():
    counter = 1
    os.chdir('F:/FACE-RECOGNITION-FINAL/Image-dataset')     # Update with your image-dataset folder path
    conn = sqlite3.connect("ImageDB.db")
    cursor = conn.cursor()

    data = cursor.execute("""SELECT * FROM ImageDB""")
    for x in data.fetchall():
        print(x[0])  # Print the name of the image
        with open("{}.png".format(counter), "wb") as f:
            f.write(x[1])
            counter = counter + 1

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()  # Call main to add images to the database
    fetch_data()  # Call fetch_data to retrieve images from the database
