// Enhanced script.js with futuristic features

let allTasks = [];
let pendingAdminWarningIds = [];

function setClassMessage(text, isError = false) {
    const msg = document.getElementById("classMsg");
    if (!msg) return;
    msg.textContent = text || "";
    msg.style.color = isError ? "#e74c3c" : "#0f9d58";
}

async function loadClasses() {
    const list = document.getElementById("classList");
    if (!list) return;
    try {
        const res = await fetch("/api/classes/my");
        if (!res.ok) {
            list.innerHTML = "<p>Unable to load classes.</p>";
            return;
        }
        const data = await res.json();
        const classes = data.classes || [];
        if (!classes.length) {
            list.innerHTML = "<p>No classes yet. Create or join one.</p>";
            return;
        }
        list.innerHTML = classes.map(c => `
            <div class="class-item">
                <div class="class-pill">${(c.role || "member").toUpperCase()}</div>
                <h3>${c.name}</h3>
                <div class="class-meta">
                    <span>Code: <strong>${c.code}</strong></span>
                    <span>Owner: ${c.owner_name || "Unknown"}</span>
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.error("Class load error:", e);
        list.innerHTML = "<p>Unable to load classes.</p>";
    }
}

async function createClassroom() {
    const input = document.getElementById("classNameInput");
    if (!input) return;
    const name = input.value.trim();
    if (!name) {
        setClassMessage("Class name is required.", true);
        return;
    }
    try {
        const res = await fetch("/api/classes/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (!res.ok) {
            setClassMessage(data.message || "Failed to create class.", true);
            return;
        }
        setClassMessage(`Class created. Join code: ${data.code}`);
        input.value = "";
        loadClasses();
    } catch (e) {
        console.error("Create class error:", e);
        setClassMessage("Failed to create class.", true);
    }
}

async function joinClassroom() {
    const input = document.getElementById("classCodeInput");
    if (!input) return;
    const code = input.value.trim();
    if (!code) {
        setClassMessage("Join code is required.", true);
        return;
    }
    try {
        const res = await fetch("/api/classes/join", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code })
        });
        const data = await res.json();
        if (!res.ok) {
            setClassMessage(data.message || "Failed to join class.", true);
            return;
        }
        setClassMessage("Joined class successfully.");
        input.value = "";
        loadClasses();
    } catch (e) {
        console.error("Join class error:", e);
        setClassMessage("Failed to join class.", true);
    }
}

// Load tasks on dashboard
async function loadTasks() {
    const taskList = document.getElementById("taskList");
    if (!taskList) return;

    const res = await fetch("/api/tasks/all");
    if (!res.ok) {
        taskList.innerHTML = "<p>Please login to view tasks.</p>";
        return;
    }

    allTasks = await res.json();
    displayTasks(allTasks);
    updateStatistics();
}

// Display tasks
function displayTasks(tasks) {
    const taskList = document.getElementById("taskList");
    
    if (tasks.length === 0) {
        taskList.innerHTML = "<p>No tasks found. Add one!</p>";
        return;
    }

    taskList.innerHTML = "";

    tasks.forEach(t => {
        const item = document.createElement("div");
        item.className = "task-card fade-in";

        // Fix date comparison
        const deadlineDate = new Date(t.deadline + 'T00:00:00');
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const timeDiff = deadlineDate - today;
        const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
        
        let riskBadge = "";
        if (t.status !== "Completed") {
            if (daysLeft < 0) {
                riskBadge = '<span class="risk-badge overdue">OVERDUE</span>';
            } else if (daysLeft === 0) {
                riskBadge = '<span class="risk-badge critical">DUE TODAY</span>';
                showNotification("Task Due Today!", `${t.title} is due today!`);
            } else if (daysLeft === 1) {
                riskBadge = '<span class="risk-badge high">DUE TOMORROW</span>';
            } else if (daysLeft <= 3) {
                riskBadge = '<span class="risk-badge high">DUE SOON</span>';
            }
        }

        item.innerHTML = `
            <div class="task-header">
                <h3>${t.title}</h3>
                <div class="task-actions">
                    <button onclick="markComplete(${t.task_id})" class="btn-small" ${t.status === 'Completed' ? 'disabled' : ''}>
                        ${t.status === 'Completed' ? '✓ Done' : 'Complete'}
                    </button>
                    <button onclick="deleteTask(${t.task_id})" class="btn-small btn-danger">Delete</button>
                </div>
            </div>
            <p>${t.description || ""}</p>
            <div class="task-meta">
                <span><b>Urgency:</b> ${t.urgency}</span>
                <span><b>Complexity:</b> ${t.complexity}</span>
                <span><b>Hours:</b> ${t.est_hours}</span>
                <span><b>Deadline:</b> ${t.deadline}</span>
                <span><b>Status:</b> ${t.status}</span>
            </div>
            <div class="task-footer">
                <div class="priority-tag ${t.priority_level?.toLowerCase() || ''}">
                    ${t.priority_level || "NA"}
                </div>
                ${riskBadge}
            </div>
        `;

        taskList.appendChild(item);
    });
}

// Search and filter tasks
async function searchTasks() {
    const query = document.getElementById("searchInput")?.value || "";
    const status = document.getElementById("statusFilter")?.value || "";
    const priority = document.getElementById("priorityFilter")?.value || "";

    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (status) params.append("status", status);
    if (priority) params.append("priority", priority);

    try {
        const res = await fetch(`/api/tasks/search?${params}`);
        if (res.ok) {
            const tasks = await res.json();
            displayTasks(tasks);
        }
    } catch(e) {
        console.error("Search error:", e);
    }
}

// Mark task as complete
async function markComplete(taskId) {
    try {
        const res = await fetch(`/api/tasks/update/${taskId}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ status: "Completed" })
        });
        
        if (res.ok) {
            showNotification("Task Completed!", "Great job! 🎉");
            loadTasks();
        } else {
            alert("Failed to update task");
        }
    } catch(e) {
        console.error("Error:", e);
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm("Are you sure you want to delete this task?")) return;
    
    try {
        const res = await fetch(`/api/tasks/delete/${taskId}`, {
            method: "DELETE"
        });
        
        if (res.ok) {
            showNotification("Task Deleted", "Task removed successfully");
            loadTasks();
        } else {
            alert("Failed to delete task");
        }
    } catch(e) {
        console.error("Error:", e);
    }
}

// Export to CSV
async function exportCSV() {
    try {
        window.location.href = "/api/tasks/export/csv";
        showNotification("Export Started", "Your CSV file is downloading");
    } catch(e) {
        console.error("Export error:", e);
    }
}

// Export tasks to ICS calendar file
async function exportICS() {
    try {
        window.location.href = "/api/tasks/calendar/export.ics";
        showNotification("Calendar Export", "ICS file download started");
    } catch (e) {
        console.error("ICS export error:", e);
    }
}

// Import tasks from pasted ICS text
async function importICS() {
    const icsText = prompt("Paste ICS calendar content:");
    if (!icsText) return;
    try {
        const res = await fetch("/api/tasks/calendar/import.ics", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ics_text: icsText, status: "Pending" })
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.message || "Failed to import ICS");
            return;
        }
        showNotification("Calendar Import", `Imported ${data.created || 0} tasks`);
        loadTasks();
    } catch (e) {
        console.error("ICS import error:", e);
        alert("Failed to import ICS");
    }
}

async function fetchNotifications() {
    const res = await fetch("/api/tasks/notifications?limit=100");
    if (!res.ok) return [];
    const data = await res.json();
    return data.notifications || [];
}

async function showAdminWarningOnLogin() {
    try {
        const items = await fetchNotifications();
        const warnings = items.filter(n => !n.is_read && (n.type === "admin" || n.type === "warning" || n.type === "info"));
        if (!warnings.length) return;

        pendingAdminWarningIds = warnings.map(w => w.notification_id);
        const modal = document.getElementById("adminWarningModal");
        const list = document.getElementById("adminWarningList");
        const content = document.getElementById("adminWarningContent");
        const title = document.getElementById("adminWarningTitle");
        const subtitle = document.getElementById("adminWarningSubtitle");
        if (!modal || !list || !content || !title || !subtitle) return;

        const severityRank = { admin: 3, warning: 2, info: 1 };
        let topType = "warning";
        warnings.forEach((w) => {
            if ((severityRank[w.type] || 0) > (severityRank[topType] || 0)) {
                topType = w.type;
            }
        });

        content.classList.remove("warning-level-admin", "warning-level-warning", "warning-level-info");
        content.classList.add(topType === "admin" ? "warning-level-admin" : topType === "info" ? "warning-level-info" : "warning-level-warning");
        title.textContent = topType === "admin" ? "Critical Admin Alert" : topType === "info" ? "Admin Notice" : "Warning";
        subtitle.textContent = topType === "admin"
            ? "You must read and acknowledge this critical admin message before continuing."
            : "Important announcement from admin:";

        list.innerHTML = warnings.map(w => `
            <div style="padding:8px; border-bottom:1px solid #fdba74;">
                <strong>${w.title || "Admin Alert"}</strong>
                <div>${w.message || ""}</div>
                <small>${w.created_at || ""}</small>
            </div>
        `).join("");
        document.body.classList.add("warning-lock");
        modal.style.display = "flex";
    } catch (e) {
        console.error("Admin warning load error:", e);
    }
}

async function acknowledgeAdminWarnings() {
    try {
        if (pendingAdminWarningIds.length) {
            await fetch("/api/tasks/notifications/mark-read", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ all: false, ids: pendingAdminWarningIds })
            });
        }
    } catch (e) {
        console.error("Admin warning acknowledge error:", e);
    } finally {
        pendingAdminWarningIds = [];
        const modal = document.getElementById("adminWarningModal");
        if (modal) modal.style.display = "none";
        document.body.classList.remove("warning-lock");
    }
}

async function openNotificationsCenter() {
    const modal = document.getElementById("notificationsModal");
    const list = document.getElementById("notificationsList");
    if (!modal || !list) return;
    const items = await fetchNotifications();
    list.innerHTML = items.length ? items.map(n => `
        <div style="padding:8px; border-bottom:1px solid #eee; background:${n.is_read ? '#fff' : '#f0f7ff'};">
            <strong>${n.title || 'Notification'}</strong>
            <div>${n.message || ''}</div>
            <small>${n.created_at || ''} ${n.is_read ? '(read)' : '(unread)'}</small>
        </div>
    `).join("") : "<p>No notifications available.</p>";
    modal.style.display = "flex";
}

async function markAllNotificationsRead() {
    try {
        const res = await fetch("/api/tasks/notifications/mark-read", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ all: true })
        });
        if (res.ok) {
            openNotificationsCenter();
        }
    } catch (e) {
        console.error("Notification update error:", e);
    }
}

// Update statistics widget
async function updateStatistics() {
    try {
        const res = await fetch("/api/tasks/analytics");
        if (!res.ok) return;

        const data = await res.json();
        
        document.getElementById("statTotal").innerText = data.total_tasks;
        
        const pending = data.by_status.find(s => s.status === "Pending");
        document.getElementById("statPending").innerText = pending ? pending.count : 0;
        
        const completed = data.by_status.find(s => s.status === "Completed");
        document.getElementById("statCompleted").innerText = completed ? completed.count : 0;
        
        document.getElementById("statAvgHours").innerText = data.avg_hours;
    } catch(e) {
        console.error("Stats error:", e);
    }
}

// Load risk alerts
async function loadRiskAlerts() {
    const riskAlert = document.getElementById("riskAlert");
    if (!riskAlert) return;

    try {
        const res = await fetch("/api/predict/risk");
        if (!res.ok) return;

        const data = await res.json();
        const criticalTasks = data.at_risk_tasks.filter(t => t.risk_level === "Critical" || t.risk_level === "High");

        if (criticalTasks.length > 0) {
            riskAlert.style.display = "block";
            riskAlert.innerHTML = `
                <h3>⚠️ Deadline Alerts</h3>
                <p>You have ${criticalTasks.length} task(s) at risk:</p>
                <ul>
                    ${criticalTasks.map(t => `
                        <li><strong>${t.title}</strong> - ${t.days_left} day(s) left (${t.risk_level} risk)</li>
                    `).join("")}
                </ul>
            `;
        }
    } catch(e) {
        console.error("Error loading risk alerts:", e);
    }
}

// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", isDark);
    showNotification("Theme Changed", isDark ? "Dark mode enabled" : "Light mode enabled");
}

// Load dark mode preference
function loadDarkMode() {
    const isDark = localStorage.getItem("darkMode") === "true";
    if (isDark) {
        document.body.classList.add("dark-mode");
    }
}

// Browser Notifications
function requestNotificationPermission() {
    if ("Notification" in window) {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                showNotification("Notifications Enabled", "You'll receive deadline alerts");
            }
        });
    }
}

function showNotification(title, body) {
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification(title, { body, icon: "/static/icon.png" });
    }
}

// Keyboard Shortcuts
document.addEventListener("keydown", (e) => {
    // Ctrl+K - Focus search
    if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        document.getElementById("searchInput")?.focus();
    }
    
    // Ctrl+N - New task
    if (e.ctrlKey && e.key === "n") {
        e.preventDefault();
        window.location.href = "/add";
    }
    
    // Ctrl+D - Toggle dark mode
    if (e.ctrlKey && e.key === "d") {
        e.preventDefault();
        toggleDarkMode();
    }
    
    // Ctrl+E - Export CSV
    if (e.ctrlKey && e.key === "e") {
        e.preventDefault();
        exportCSV();
    }
    
    // ? - Show shortcuts help
    if (e.key === "?" && !e.ctrlKey && !e.shiftKey) {
        document.getElementById("shortcutsHelp").style.display = "flex";
    }
    
    // Esc - Close modals
    if (e.key === "Escape") {
        document.getElementById("shortcutsHelp").style.display = "none";
    }
});

function closeShortcutsHelp() {
    document.getElementById("shortcutsHelp").style.display = "none";
}

// Voice Input (Web Speech API)
function startVoiceInput() {
    if (!('webkitSpeechRecognition' in window)) {
        alert("Voice input not supported in this browser");
        return;
    }

    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById("searchInput").value = transcript;
        searchTasks();
    };

    recognition.start();
    showNotification("Listening...", "Speak your search query");
}

// Auto-load tasks and alerts when dashboard loads
document.addEventListener("DOMContentLoaded", () => {
    loadDarkMode();
    
    if (document.getElementById("taskList")) {
        loadTasks();
        loadRiskAlerts();
        showAdminWarningOnLogin();
        loadClasses();
        
        // Check for deadline alerts every 5 minutes
        setInterval(loadRiskAlerts, 5 * 60 * 1000);
    }
});

// ========== POMODORO TIMER FUNCTIONS ==========

let timerInterval = null;
let timeLeft = 25 * 60; // 25 minutes in seconds
let isWorkSession = true;

function startTimer() {
    if (timerInterval) return; // Already running
    
    timerInterval = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();
        
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            timerInterval = null;
            
            // Play notification
            showNotification(
                isWorkSession ? "Break Time!" : "Work Time!",
                isWorkSession ? "Take a 5-minute break" : "Start your 25-minute focus session"
            );
            
            // Switch session
            isWorkSession = !isWorkSession;
            timeLeft = isWorkSession ? 25 * 60 : 5 * 60;
            updateTimerDisplay();
        }
    }, 1000);
}

function pauseTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function resetTimer() {
    pauseTimer();
    isWorkSession = true;
    timeLeft = 25 * 60;
    updateTimerDisplay();
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    document.getElementById("timerDisplay").innerText = 
        `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// ========== AI CHATBOT FUNCTIONS ==========

function toggleChatbot() {
    const body = document.getElementById("chatbotBody");
    const toggle = document.getElementById("chatToggle");
    
    if (body.style.display === "none") {
        body.style.display = "flex";
        toggle.innerText = "▲";
    } else {
        body.style.display = "none";
        toggle.innerText = "▼";
    }
}

async function sendMessage() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, "user");
    input.value = "";
    
    // Show typing indicator
    addChatMessage("Thinking...", "bot", true);
    
    try {
        const res = await fetch("/api/chatbot/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ message })
        });
        
        const data = await res.json();
        
        // Remove typing indicator
        const messages = document.getElementById("chatMessages");
        const typingMsg = messages.querySelector(".typing");
        if (typingMsg) typingMsg.remove();
        
        // Add bot response
        addChatMessage(data.response, "bot");
        
    } catch(e) {
        console.error("Chat error:", e);
        addChatMessage("Sorry, I encountered an error. Please try again.", "bot");
    }
}

function addChatMessage(text, sender, isTyping = false) {
    const messages = document.getElementById("chatMessages");
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-message" : "bot-message";
    if (isTyping) msgDiv.classList.add("typing");
    msgDiv.innerText = text;
    messages.appendChild(msgDiv);
    messages.scrollTop = messages.scrollHeight;
}


// Gamification Functions
async function loadGamificationStats() {
    try {
        const res = await fetch('/api/gamify/stats');
        const data = await res.json();
        
        document.getElementById('pointsDisplay').textContent = data.points || 0;
        document.getElementById('levelBadge').textContent = `Level ${data.level || 1}`;
        document.getElementById('streakDisplay').textContent = `🔥 ${data.streak || 0} day streak`;
    } catch (e) {
        console.log('Gamification not available');
    }
}

function showPointsEarned(points) {
    const popup = document.createElement('div');
    popup.className = 'points-popup';
    popup.textContent = `+${points} Points!`;
    document.body.appendChild(popup);
    
    setTimeout(() => popup.remove(), 2000);
    loadGamificationStats();
}

// Swipe Gesture Support
let touchStartX = 0;
let touchEndX = 0;
let swipingCard = null;

function handleSwipeStart(e, taskId) {
    touchStartX = e.changedTouches[0].screenX;
    swipingCard = e.currentTarget;
}

function handleSwipeMove(e) {
    if (!swipingCard) return;
    touchEndX = e.changedTouches[0].screenX;
    const diff = touchEndX - touchStartX;
    
    if (diff < -50) {
        swipingCard.classList.add('swiping-left');
    } else if (diff > 50) {
        swipingCard.classList.add('swiping-right');
    } else {
        swipingCard.classList.remove('swiping-left', 'swiping-right');
    }
}

async function handleSwipeEnd(e, taskId) {
    if (!swipingCard) return;
    
    const diff = touchEndX - touchStartX;
    
    // Swipe left = Delete
    if (diff < -100) {
        if (confirm('Delete this task?')) {
            await deleteTask(taskId);
            createConfetti();
        }
    }
    // Swipe right = Complete
    else if (diff > 100) {
        await completeTask(taskId);
        createConfetti();
        showPointsEarned(50);
    }
    
    swipingCard.classList.remove('swiping-left', 'swiping-right');
    swipingCard = null;
    touchStartX = 0;
    touchEndX = 0;
}

async function completeTask(taskId) {
    try {
        const res = await fetch(`/api/tasks/update/${taskId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: 'Completed'})
        });
        
        if (res.ok) {
            showNotification('Task completed! 🎉', 'success');
            loadTasks();
        }
    } catch (e) {
        console.error('Error completing task:', e);
    }
}

// Load gamification on page load
document.addEventListener('DOMContentLoaded', () => {
    loadGamificationStats();
    
    // Add swipe listeners to task cards
    document.addEventListener('touchstart', (e) => {
        if (e.target.closest('.task-card')) {
            const card = e.target.closest('.task-card');
            const taskId = card.dataset.taskId;
            if (taskId) handleSwipeStart(e, taskId);
        }
    });
    
    document.addEventListener('touchmove', handleSwipeMove);
    
    document.addEventListener('touchend', (e) => {
        if (swipingCard) {
            const taskId = swipingCard.dataset.taskId;
            handleSwipeEnd(e, taskId);
        }
    });
});


// Animate Progress Circle
function updateProgressCircle(points) {
    const circle = document.getElementById('progressCircle');
    const maxPoints = 1000;
    const progress = Math.min(points / maxPoints, 1);
    const offset = 283 - (283 * progress);
    if (circle) {
        circle.style.strokeDashoffset = offset;
        circle.style.transition = 'stroke-dashoffset 1s ease';
    }
}

// Update gamification with animation
async function loadGamificationStats() {
    try {
        const res = await fetch('/api/gamify/stats');
        const data = await res.json();
        
        const points = data.points || 0;
        document.getElementById('pointsDisplay').textContent = points;
        document.getElementById('levelBadge').textContent = `Level ${data.level || 1}`;
        document.getElementById('streakDisplay').textContent = `${data.streak || 0} days`;
        
        updateProgressCircle(points);
    } catch (e) {
        console.log('Gamification not available');
    }
}
