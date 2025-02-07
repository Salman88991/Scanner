from flask import Flask, render_template, request, redirect, url_for
import pytesseract
import cv2
import sqlite3
import os

app = Flask(__name__)

# Set the path for tesseract OCR (replace with your path)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # for Windows

# Database setup function
def init_db():
    conn = sqlite3.connect('transactions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, description TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to upload an image and process it
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return redirect(request.url)
    
    file = request.files['image']
    
    if file:
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        
        # Process the image for transaction details
        transaction_info = process_image(filepath)
        
        # Store transaction in the database
        if transaction_info:
            description, amount, date = transaction_info
            conn = sqlite3.connect('transactions.db')
            c = conn.cursor()
            c.execute("INSERT INTO transactions (description, amount, date) VALUES (?, ?, ?)", 
                      (description, amount, date))
            conn.commit()
            conn.close()

            return f"Transaction recorded: {description}, {amount}, {date}"
        else:
            return "No transaction details found in the image."
    
    return redirect(url_for('index'))

# Function to process image and extract transaction details
def process_image(image_path):
    # Read the image
    img = cv2.imread(image_path)

    # Convert the image to grayscale for better OCR performance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Use Tesseract to extract text from the image
    text = pytesseract.image_to_string(gray)

    # Example of parsing the text (this would need to be tailored to your specific use case)
    lines = text.split('\n')
    description, amount, date = "", 0.0, ""

    for line in lines:
        if "Total" in line or "Amount" in line:
            amount = float(line.split(":")[1].strip().replace('$', '').replace(',', ''))
        if "Date" in line:
            date = line.split(":")[1].strip()
        if len(line.split()) > 2:  # Assuming description is multi-word
            description = line.strip()

    if description and amount > 0.0 and date:
        return description, amount, date
    else:
        return None

# Initialize the database on first run
init_db()

if __name__ == '__main__':
    app.run(debug=True)
