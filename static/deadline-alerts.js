// Deadline Alert System with Sound Effects

// Create audio context for sound effects
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

// Generate alert sound (beep)
function playAlertSound(frequency = 800, duration = 200) {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = frequency;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + duration / 1000);
}

// Play urgent alert (3 beeps)
function playUrgentAlert() {
    playAlertSound(800, 150);
    setTimeout(() => playAlertSound(900, 150), 200);
    setTimeout(() => playAlertSound(1000, 200), 400);
}

// Check deadlines and alert based on estimated hours
async function checkDeadlineAlerts() {
    try {
        const res = await fetch('/api/tasks/all');
        const tasks = await res.json();
        
        const now = new Date();
        
        tasks.forEach(task => {
            if (task.status === 'Completed') return;
            
            const deadline = new Date(task.deadline);
            const hoursUntilDeadline = (deadline - now) / (1000 * 60 * 60);
            const estHours = task.est_hours || 0;
            const daysLeft = Math.ceil(hoursUntilDeadline / 24);
            
            // Critical: Need to start NOW (time left <= estimated time)
            if (hoursUntilDeadline > 0 && hoursUntilDeadline <= estHours) {
                showDeadlineNotification(
                    task, 
                    `START NOW! Need ${estHours}h, only ${Math.round(hoursUntilDeadline)}h left`, 
                    'critical'
                );
                playUrgentAlert();
            }
            // Urgent: Less than 2 hours buffer
            else if (hoursUntilDeadline > 0 && hoursUntilDeadline <= (estHours + 2)) {
                showDeadlineNotification(
                    task, 
                    `URGENT! Start soon - ${Math.round(hoursUntilDeadline)}h until deadline`, 
                    'high'
                );
                playAlertSound(800, 200);
            }
            // Alert for tasks due today
            else if (daysLeft === 0 && hoursUntilDeadline > 0) {
                showDeadlineNotification(task, 'DUE TODAY', 'high');
                playAlertSound(700, 200);
            }
            // Alert for tasks due tomorrow
            else if (daysLeft === 1) {
                showDeadlineNotification(task, 'DUE TOMORROW', 'medium');
            }
            // Alert for overdue tasks
            else if (hoursUntilDeadline < 0) {
                showDeadlineNotification(task, 'OVERDUE', 'critical');
                playUrgentAlert();
            }
        });
    } catch (e) {
        console.error('Error checking deadlines:', e);
    }
}

// Show deadline notification
function showDeadlineNotification(task, timeText, severity) {
    const notification = document.createElement('div');
    notification.className = `deadline-notification ${severity}`;
    notification.innerHTML = `
        <div class="notification-icon">⚠️</div>
        <div class="notification-content">
            <strong>${task.title}</strong>
            <p>Due ${timeText}!</p>
        </div>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 10000);
}

// Check deadlines every 30 minutes
setInterval(checkDeadlineAlerts, 30 * 60 * 1000);

// Check on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(checkDeadlineAlerts, 2000); // Check after 2 seconds
});

// Manual check function
function checkDeadlinesNow() {
    checkDeadlineAlerts();
}
