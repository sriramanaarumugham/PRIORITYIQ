# PriorityIQ - AI Task Prioritizer 📱

> **Now available as a Progressive Web App (PWA)!** Install on any device for a native app experience.

## Setup Instructions

### 1. Clone/Download Project
```bash
cd priorityIQ
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy the example file
copy .env.example .env

# Edit .env and update with your settings:
# - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
# - Generate a strong SECRET_KEY (see below)
```

**Generate a secure SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### 4. Create MySQL Database
Open MySQL Workbench and run:
```sql
CREATE DATABASE priorityiq;
USE priorityiq;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    deadline DATE,
    urgency INT,
    complexity INT,
    est_hours FLOAT,
    priority_level VARCHAR(20),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE priority_predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    predicted_priority VARCHAR(20),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
```

### 5. Train ML Model
```bash
python ml/train_model.py
```

### 6. Generate PWA Icons (Optional)
```bash
python ml/generate_icons.py
```

### 7. Run Application
```bash
python app.py
```

Access at: http://127.0.0.1:5000

## 📱 PWA Installation

PriorityIQ can be installed on any device:

- **Mobile**: Tap "📱 Install App" button or use browser's "Add to Home Screen"
- **Desktop**: Click install icon in address bar or "📱 Install App" button
- **Features**: Offline support, full-screen mode, push notifications

See [PWA_QUICKSTART.md](PWA_QUICKSTART.md) for detailed instructions.

## Key Features

### 🔐 Security
- 3-factor authentication (Email, OTP, Face Recognition)
- Environment-based configuration
- Cryptographically secure OTP generation
- Parameterized SQL queries
- Secure session management

### 🤖 AI/ML
- Smart priority prediction (Decision Tree)
- Conversational AI chatbot
- Natural language task creation
- Deadline risk detection

### 📊 Productivity
- Kanban board with drag-and-drop
- Interactive calendar view
- Pomodoro timer widget
- Task categories and tags
- Search and filter
- CSV export
- **Smart reminders based on estimated hours** ⚡

### 📱 PWA
- Install on any device
- Offline support
- Full-screen mode
- Mobile-optimized
- Push notifications

### 🎨 UX
- Dark mode
- Keyboard shortcuts
- Voice input
- Real-time notifications
- Responsive design

## Security Features

- Environment-based configuration (no hardcoded credentials)
- Cryptographically secure OTP generation
- Secure session management
- Input validation and sanitization
- Parameterized SQL queries (SQL injection prevention)
- Proper error handling
- Resource cleanup

## Project Structure
```
priorityIQ/
├── app.py                 # Main Flask application
├── db_connection.py       # Database connection handler
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (DO NOT COMMIT)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── routes/
│   ├── auth_routes.py    # Authentication endpoints
│   ├── task_routes.py    # Task management endpoints
│   ├── predict_routes.py # ML prediction endpoints
│   └── chatbot_routes.py # AI chatbot endpoints
├── ml/
│   ├── train_model.py    # Model training script
│   ├── predict.py        # Prediction testing
│   ├── generate_icons.py # PWA icon generator
│   └── model.pkl         # Trained model (generated)
├── templates/            # HTML templates
├── static/              # CSS, JS files
│   ├── manifest.json    # PWA manifest
│   ├── service-worker.js # Service worker
│   ├── pwa.js           # PWA install logic
│   ├── icon-192.png     # App icon (small)
│   └── icon-512.png     # App icon (large)
└── PWA_QUICKSTART.md    # PWA installation guide
```

## API Endpoints

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/request_otp` - Request OTP for login
- POST `/api/auth/verify_otp` - Verify OTP
- POST `/api/auth/verify_face` - Face recognition verification
- GET `/api/auth/status` - Check login status
- POST `/api/auth/logout` - Logout

### Tasks
- POST `/api/tasks/add` - Add new task
- GET `/api/tasks/all` - Get all user tasks
- GET `/api/tasks/search` - Search and filter tasks
- GET `/api/tasks/export/csv` - Export tasks to CSV
- GET `/api/tasks/analytics` - Get task analytics
- PUT `/api/tasks/update` - Update task status

### Predictions
- POST `/api/predict/quick` - Quick priority prediction
- POST `/api/predict/priority` - Detailed priority prediction
- POST `/api/predict/risk` - Deadline risk detection

### Chatbot
- POST `/api/chatbot/chat` - AI assistant conversation

## Important Notes

1. **Never commit .env file** - Contains sensitive credentials
2. **Change SECRET_KEY** - Generate a new one for production
3. **Disable debug mode** - Set FLASK_ENV=production in production
4. **Use HTTPS** - Required for PWA and secure cookies in production
5. **Update dependencies** - Regularly check for security updates
6. **PWA requires HTTPS** - Use localhost for development, HTTPS for production

## Additional Documentation

- [SECURITY_FIXES.md](SECURITY_FIXES.md) - Security improvements
- [NEW_FEATURES_GUIDE.md](NEW_FEATURES_GUIDE.md) - Latest features guide
- [PWA_SETUP.md](PWA_SETUP.md) - Detailed PWA documentation
- [PWA_QUICKSTART.md](PWA_QUICKSTART.md) - Quick PWA installation guide
- [SMART_REMINDERS.md](SMART_REMINDERS.md) - Smart reminder system guide ⚡

## Total Features: 49+

✅ User registration & authentication  
✅ Face recognition security  
✅ OTP verification  
✅ Task CRUD operations  
✅ ML priority prediction  
✅ AI chatbot assistant  
✅ Kanban board  
✅ Calendar view  
✅ Pomodoro timer  
✅ Task categories  
✅ Search & filter  
✅ CSV export  
✅ Analytics dashboard  
✅ Dark mode  
✅ Keyboard shortcuts  
✅ Voice input  
✅ Push notifications  
✅ **PWA support**  
✅ **Offline mode**  
✅ **Mobile installation**  
✅ **Smart reminders (estimated hours-based)** ⚡  

For detailed security fixes, see [SECURITY_FIXES.md](SECURITY_FIXES.md)
