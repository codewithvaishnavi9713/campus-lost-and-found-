# 🎓 Smart Campus Lost & Found

A modern, AI-ready lost and found web application designed specifically for university and college campuses.

---

## 🚀 Phase 0 Status: Complete Foundation Setup

Phase 0 establishes the core application structure, Flask application factory pattern, dark campus-tech design system, Jinja templating, and placeholder interactive buttons.

---

## 🛠️ Architecture & Project Structure

```
smart-campus-lost-found/
│
├── app/
│   ├── __init__.py           # Flask Application Factory (create_app)
│   ├── config.py             # Environment configuration settings
│   ├── extensions.py         # Extension initialization hub (future ORM/Auth)
│   ├── routes/
│   │   └── __init__.py       # Main blueprint & homepage routes
│   ├── ai/
│   │   └── __init__.py       # AI matching module placeholder
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Campus-tech dark theme & glassmorphic design
│   │   └── js/
│   │       └── main.js       # Toast alerts & UI interactive handlers
│   └── templates/
│       ├── base.html         # Master layout template
│       └── index.html        # Smart Campus homepage banner & grid
│
├── instance/                 # SQLite database & local storage directory
├── tests/                    # Unit and integration tests directory
│
├── requirements.txt          # Python dependencies
├── run.py                    # Server startup entrypoint
├── .gitignore                # Git ignore patterns
└── README.md                 # Project documentation
```

---

## ⚡ Quickstart & How to Run

1. **Navigate to project directory:**
   ```bash
   cd smart-campus-lost-found
   ```

2. **(Optional) Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask application:**
   ```bash
   python run.py
   ```

5. **Open in browser:**
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🗺️ Roadmap & Upcoming Phases

- **Phase 0:** Project Foundation, Dark Theme UI, Flask Factory *(Current)*
- **Phase 1:** User Authentication (Login/Register) & Database Models (SQLite)
- **Phase 2:** Lost & Found Item Reporting Forms with Image Uploads
- **Phase 3:** Smart AI Item Matching Engine & Similarity Scoring
- **Phase 4:** Interactive Dashboard, Claiming Workflow & Notifications
