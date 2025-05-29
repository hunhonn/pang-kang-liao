# Pang Kang Liao Web App

This project is a web application that allows users to input multiple origins and destinations to find a meeting point based on a specified time threshold. The application utilizes a free maps API and is built using Flask for the backend and htmx for dynamic content loading on the frontend.

## Project Structure

```
pang-kang-liao-webapp
├── public
│   ├── index.html        # Main HTML document for the web application
│   ├── styles.css        # CSS styles for the web application
│   └── scripts.js        # JavaScript for client-side logic
├── server
│   ├── app.py            # Main entry point for the Flask web server
│   └── templates
│       └── result.html   # Template for displaying results
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd pang-kang-liao-webapp
   ```

2. **Install the required Python packages:**
   Make sure you have Python and pip installed. Then run:
   ```
   pip install -r requirements.txt
   ```

3. **Run the Flask server (from root folder):**
   ```
   source server/venv/bin/activate
   python server/app.py
   ```

4. **Open your web browser:**
   Navigate to `http://127.0.0.1:5000` to access the web application.

## Usage

- Input multiple origins and destinations in the provided form.
- Specify a time threshold for the meeting point.
- Submit the form to see the calculated meeting point based on the input data.

## License

This project is open-source and available under the MIT License.