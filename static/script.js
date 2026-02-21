// Update datetime every minute
function updateDateTime() {
    fetch('/datetime')
        .then(response => response.json())
        .then(data => {
            document.getElementById('time').innerHTML = `<i class="far fa-clock"></i> ${data.time}`;
            document.getElementById('date').innerHTML = `<i class="far fa-calendar"></i> ${data.date}`;
        })
        .catch(error => console.error('Error:', error));
}

setInterval(updateDateTime, 60000);

// Auto-scroll chat to bottom
function scrollToBottom() {
    const chatDisplay = document.getElementById('chatDisplay');
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

// Show toast notification
function showToast(message, icon = 'check-circle') {
    const toast = document.getElementById('toast');
    toast.innerHTML = `<i class="fas fa-${icon}"></i> <span>${message}</span>`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Handle form submissions
document.addEventListener('DOMContentLoaded', function() {
    scrollToBottom();
    
    // Set active button
    document.getElementById('chatBtn').classList.add('active');
    
    // Message form
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            const input = document.getElementById('messageInput');
            if (!input.value.trim()) {
                e.preventDefault();
                showToast('Please type a message!', 'exclamation-circle');
                return;
            }
            
            // Show loading
            const sendBtn = document.getElementById('sendBtn');
            const originalText = sendBtn.innerHTML;
            sendBtn.innerHTML = '<span class="loading"></span> Sending';
            sendBtn.disabled = true;
            
            // Show toast
            showToast('Sending message...', 'paper-plane');
            
            // Re-enable after timeout
            setTimeout(() => {
                sendBtn.innerHTML = originalText;
                sendBtn.disabled = false;
            }, 2000);
        });
    }
    
    // History button
    document.getElementById('historyBtn')?.addEventListener('click', function() {
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        this.classList.add('active');
        showToast('Loading history...', 'clock-rotate-left');
    });
    
    // Chat button
    document.getElementById('chatBtn')?.addEventListener('click', function() {
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        this.classList.add('active');
    });
    
    // Erase button
    document.getElementById('eraseBtn')?.addEventListener('click', function(e) {
        if (!confirm('✨ Are you sure you want to delete all chats?')) {
            e.preventDefault();
        }
    });
    
    // Speak button
    document.getElementById('speakBtn')?.addEventListener('click', function() {
        showToast('Playing response...', 'volume-high');
    });
    
    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            document.getElementById('messageInput').value = this.textContent;
            document.getElementById('sendBtn').click();
        });
    });
});

// Enter key
document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('sendBtn').click();
    }
});

// Typing indicator
let typingTimeout;
document.getElementById('messageInput')?.addEventListener('input', function() {
    clearTimeout(typingTimeout);
    
    // Add typing animation if needed
    typingTimeout = setTimeout(() => {
        // Reset typing state
    }, 1000);
});

// Auto-refresh for new messages
let lastMessageCount = document.querySelectorAll('.chat-messages p').length;

setInterval(() => {
    const currentCount = document.querySelectorAll('.chat-messages p').length;
    if (currentCount > lastMessageCount) {
        scrollToBottom();
        lastMessageCount = currentCount;
        
        // Show notification for new message
        showToast('New message received!', 'bell');
    }
}, 2000);

// Parallax effect on mouse move
document.addEventListener('mousemove', function(e) {
    const mouseX = e.clientX / window.innerWidth;
    const mouseY = e.clientY / window.innerHeight;
    
    const circles = document.querySelectorAll('.floating-circle');
    circles.forEach((circle, index) => {
        const speed = (index + 1) * 20;
        const x = (mouseX * speed) - (speed / 2);
        const y = (mouseY * speed) - (speed / 2);
        circle.style.transform = `translate(${x}px, ${y}px)`;
    });
});

// Smooth scroll to top when new chat starts
function scrollToTop() {
    const chatDisplay = document.getElementById('chatDisplay');
    chatDisplay.scrollTop = 0;
}

// Window resize handler
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        scrollToBottom();
    }, 250);
});

// Add shine effect to buttons
document.querySelectorAll('.option-btn, .send-btn, .speak-btn').forEach(btn => {
    btn.classList.add('shine');
});

// Random greeting messages
const greetings = [
    "✨ Kaise hain aap?",
    "💭 Kya soch rahe hain?",
    "🎵 Gana sunenge?",
    "📝 Kuch likhna chahenge?",
    "🤔 Koi sawaal?",
    "😊 Batao batao!"
];

// Change typing animation text periodically
let greetingIndex = 0;
setInterval(() => {
    const typingElement = document.querySelector('.typing-animation');
    if (typingElement) {
        greetingIndex = (greetingIndex + 1) % greetings.length;
        typingElement.textContent = greetings[greetingIndex];
    }
}, 3000);

// Audio player ended event
document.getElementById('audioPlayer')?.addEventListener('ended', function() {
    this.remove();
    showToast('Audio finished playing', 'check');
});

// Add ripple effect to buttons
function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

document.querySelectorAll('.option-btn, .send-btn, .speak-btn').forEach(btn => {
    btn.addEventListener('click', createRipple);
});

// Update the shutdown modal to handle both
let currentAction = null; // 'shutdown' or 'restart'

function sendShutdown(answer){
    fetch('/confirm_shutdown', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({answer:answer})
    });

    document.getElementById("shutdownModal").style.display="none";
}

setInterval(() => {
    fetch('/get_instruction')
    .then(res => res.json())
    .then(data => {
        if(data.instruction === "show_shutdown_popup"){
            currentAction = 'shutdown';
            document.getElementById("shutdownModal").style.display="block";
            document.querySelector("#shutdownModal h3").textContent = "Are you sure you want to shutdown?";
        } else if(data.instruction === "show_restart_popup"){
            currentAction = 'restart';
            document.getElementById("shutdownModal").style.display="block";
            document.querySelector("#shutdownModal h3").textContent = "Are you sure you want to restart?";
        }
    });
}, 1000);