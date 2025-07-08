// Over-Under Contests JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Contest form dynamic questions
    initializeContestForm();
    
    // Entry form enhancements
    initializeEntryForm();
    
    // Admin panel features
    initializeAdminFeatures();
});

// Contest form functionality - removed old implementation
// Contest form is now handled by template-specific JavaScript
function initializeContestForm() {
    // Contest form functionality is now handled in the template
    // This prevents conflicts with the updated form implementation
}

// Entry form functionality
function initializeEntryForm() {
    const entryForm = document.getElementById('entry-form');
    if (entryForm) {
        // Add confirmation before submitting
        entryForm.addEventListener('submit', function(e) {
            const unanswered = entryForm.querySelectorAll('.question-card').length - 
                              entryForm.querySelectorAll('input[type="radio"]:checked').length;
            
            if (unanswered > 0) {
                if (!confirm(`You have ${unanswered} unanswered questions. Submit anyway?`)) {
                    e.preventDefault();
                }
            }
        });
        
        // Progress tracking
        updateEntryProgress();
        
        const radioButtons = entryForm.querySelectorAll('input[type="radio"]');
        radioButtons.forEach(function(radio) {
            radio.addEventListener('change', updateEntryProgress);
        });
    }
}

function updateEntryProgress() {
    const entryForm = document.getElementById('entry-form');
    const progressBar = document.getElementById('entry-progress');
    
    if (entryForm && progressBar) {
        const totalQuestions = entryForm.querySelectorAll('.question-card').length;
        const answeredQuestions = entryForm.querySelectorAll('input[type="radio"]:checked').length;
        const percentage = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
        
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `${answeredQuestions} of ${totalQuestions} questions answered`;
        }
    }
}

// Admin panel functionality
function initializeAdminFeatures() {
    // Toggle contest active status
    const toggleButtons = document.querySelectorAll('.toggle-contest-active');
    toggleButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const contestId = button.getAttribute('data-contest-id');
            toggleContestActive(contestId, button);
        });
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.confirm-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = button.getAttribute('data-confirm-message') || 
                           'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

function toggleContestActive(contestId, button) {
    const originalText = button.textContent;
    button.textContent = 'Loading...';
    button.disabled = true;
    
    fetch(`/admin/contests/${contestId}/toggle-active`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const badge = button.closest('tr').querySelector('.status-badge');
            if (data.is_active) {
                button.textContent = 'Deactivate';
                button.className = 'btn btn-sm btn-warning toggle-contest-active';
                if (badge) {
                    badge.textContent = 'Active';
                    badge.className = 'badge bg-success status-badge';
                }
            } else {
                button.textContent = 'Activate';
                button.className = 'btn btn-sm btn-success toggle-contest-active';
                if (badge) {
                    badge.textContent = 'Inactive';
                    badge.className = 'badge bg-danger status-badge';
                }
            }
        } else {
            button.textContent = originalText;
            alert('Failed to update contest status.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.textContent = originalText;
        alert('An error occurred while updating contest status.');
    })
    .finally(() => {
        button.disabled = false;
    });
}

// Utility functions
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

function showLoading(element) {
    element.classList.add('loading');
    const spinner = document.createElement('span');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    element.insertBefore(spinner, element.firstChild);
}

function hideLoading(element) {
    element.classList.remove('loading');
    const spinner = element.querySelector('.spinner-border');
    if (spinner) {
        spinner.remove();
    }
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateUsername(username) {
    const re = /^[a-zA-Z0-9_]{3,20}$/;
    return re.test(username);
}

// Date/time helpers
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function timeUntil(dateString) {
    const now = new Date();
    const target = new Date(dateString);
    const diff = target - now;
    
    if (diff <= 0) {
        return 'Expired';
    }
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Loading overlay functionality
function showLoadingOverlay(message = 'Loading...') {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div id="loading-message">${message}</div>
            </div>
        `;
        document.body.appendChild(overlay);
    } else {
        document.getElementById('loading-message').textContent = message;
    }
    
    setTimeout(() => overlay.classList.add('show'), 10);
    return overlay;
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('show');
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 300);
    }
}

// Enhanced form submission with loading states
function enhanceFormSubmission() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.hasAttribute('data-no-loading')) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
                
                // Re-enable button after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', function() {
    enhanceFormSubmission();
});

// Export functions for use in templates
window.OverUnderContests = {
    updateEntryProgress,
    toggleContestActive,
    showLoading,
    hideLoading,
    showLoadingOverlay,
    hideLoadingOverlay,
    validateEmail,
    validateUsername,
    formatDateTime,
    timeUntil
};
