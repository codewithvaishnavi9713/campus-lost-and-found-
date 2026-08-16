/**
 * Smart Campus Lost & Found - Main JavaScript
 * Handles interactive placeholders, notifications, and navigation state.
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('Smart Campus Lost & Found - Phase 0 initialized.');

  // Attach click handlers to placeholder report buttons
  
});

/**
 * Creates and displays a sleek toast notification.
 * @param {string} title - Toast header text
 * @param {string} message - Detailed notification body
 * @param {string} icon - Emoji or icon character
 */
function showToast(title, message, icon = 'ℹ️') {
  let toastContainer = document.querySelector('.toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-body">
      <div class="toast-title">${escapeHTML(title)}</div>
      <div class="toast-msg">${escapeHTML(message)}</div>
    </div>
  `;

  toastContainer.appendChild(toast);

  // Auto remove toast after 4 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Escapes HTML characters to prevent XSS.
 * @param {string} str 
 * @returns {string}
 */
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
