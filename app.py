from flask import Flask, render_template, request
import os
from mains import process_video  # Ensure this is 'main.py' and not 'mains.py'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return "No file part"

    file = request.files['video']
    if file.filename == '':
        return "No selected file"

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Process the video
        result = process_video(filepath)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Complete</title>
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f0f2f5;
                    text-align: center;
                    padding: 50px;
                }}
                .result-box {{
                    background-color: white;
                    padding: 30px;
                    margin: auto;
                    border-radius: 15px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    max-width: 700px;
                }}
                h2 {{
                    color: #2c3e50;
                }}
                p {{
                    font-size: 1.1em;
                    color: #34495e;
                }}
                .images {{
                    margin-top: 20px;
                }}
                .images img {{
                    width: 90%;
                    max-width: 600px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    border: 1px solid #ccc;
                }}
                a.button {{
                    display: inline-block;
                    margin-top: 30px;
                    padding: 12px 20px;
                    background-color: #007BFF;
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                    border-radius: 8px;
                    transition: background-color 0.3s ease;
                }}
                a.button:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="result-box">
                <h2>✅ Video Processed Successfully</h2>
                <p><strong>File:</strong> {file.filename}</p>
                <p><strong>Total Vehicles:</strong> {result['total_vehicles']}</p>
                <p><strong>Estimated AQI:</strong> {result['estimated_aqi']}</p>
                <p><strong>Air Quality:</strong> {result['air_quality']}</p>
                <p><strong>Overspeeding Vehicle IDs:</strong> {', '.join(map(str, result['overspeeding_ids'])) or 'None'}</p>

                <div class="images">
                    <h3>📊 Graphs</h3>
                    <img src="/static/vehicle_count_bar_chart.png" alt="Vehicle Count Bar Chart">
                    <img src="/static/aqi_over_time_line_graph.png" alt="AQI Over Time Line Graph">
                </div>

                <a class="button" href="/">⬅️ Upload Another Video</a>
            </div>
        </body>
        </html>
        """

if __name__ == '__main__':
    app.run(debug=True, port=5050)  # Changed port to avoid 5000 conflict
