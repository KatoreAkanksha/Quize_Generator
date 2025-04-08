# Quiz Generator Platform

A full-stack web application built with Flask and MySQL that allows teachers to create quizzes from uploaded files and students to take those quizzes.

## Features

### Teacher Dashboard
- Upload files (supports .docx, .pptx, .png, .pdf)
- Generate quiz questions using Gemini Flash 2.0 API
- Set quiz parameters (title, difficulty, timer)
- Share quizzes with students
- View student results and statistics

### Student Dashboard
- Register and login
- View available quizzes
- Take quizzes with timer
- View results after submission
- Track progress across multiple quizzes

## Tech Stack

- Backend: Python Flask
- Database: MySQL
- Authentication: Flask-Login
- File Processing: PyPDF2, python-docx, Pillow
- Styling: Tailwind CSS

## Installation

1. Clone the repository

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up MySQL database:
- Create a database named 'quiz_db'
- Update .env file with your database credentials

5. Run the application:
```bash
python app.py
```

6. Access the application:
- Open http://localhost:5000 in your browser
- Register as a teacher or student to begin

## Environment Variables

Create a .env file in the root directory with the following variables:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=pass@786
DB_NAME=quiz_db
VITE_GEMINI_API_KEY=your_gemini_api_key
```

## Project Structure

```
quizman/
├── app.py                 # Main application file
├── models.py              # Database models
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables
├── services/
│   └── gemini_service.py  # Mock Gemini API service
├── blueprints/
│   ├── auth.py           # Authentication routes
│   ├── teacher.py         # Teacher dashboard routes
│   ├── student.py         # Student dashboard routes
│   └── quiz.py           # Quiz management routes
└── templates/             # HTML templates
```

## Security

- Passwords are hashed using SHA-256
- Session management with Flask-Login
- File upload validation and sanitization
- Environment variables for sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request