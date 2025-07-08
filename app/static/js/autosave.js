// Auto-save functionality for contest entries
class AutoSave {
    constructor(formId, options = {}) {
        this.form = document.getElementById(formId);
        this.options = {
            saveInterval: 30000, // 30 seconds
            endpoint: '/api/autosave-entry',
            indicatorId: 'autosave-indicator',
            debounceDelay: 2000, // 2 seconds after last change
            ...options
        };
        
        this.saveTimeout = null;
        this.lastSaveData = null;
        this.indicator = null;
        this.isEnabled = true;
        
        if (this.form) {
            this.init();
        }
    }
    
    init() {
        this.createIndicator();
        this.attachEventListeners();
        this.loadSavedData();
        
        // Auto-save periodically
        setInterval(() => {
            if (this.isEnabled && this.hasChanges()) {
                this.save();
            }
        }, this.options.saveInterval);
    }
    
    createIndicator() {
        // Create autosave indicator if it doesn't exist
        this.indicator = document.getElementById(this.options.indicatorId);
        if (!this.indicator) {
            this.indicator = document.createElement('div');
            this.indicator.id = this.options.indicatorId;
            this.indicator.className = 'autosave-indicator';
            document.body.appendChild(this.indicator);
        }
    }
    
    attachEventListeners() {
        // Listen for form changes
        const inputs = this.form.querySelectorAll('input[type="radio"], input[type="checkbox"], select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.scheduleAutoSave();
            });
        });
        
        // Prevent form submission if autosave is in progress
        this.form.addEventListener('submit', (e) => {
            if (this.isSaving) {
                e.preventDefault();
                this.showIndicator('Please wait for auto-save to complete...', 'saving');
                
                // Wait for save to complete, then submit
                const checkSave = () => {
                    if (!this.isSaving) {
                        this.form.submit();
                    } else {
                        setTimeout(checkSave, 100);
                    }
                };
                setTimeout(checkSave, 100);
            }
        });
        
        // Save before page unload
        window.addEventListener('beforeunload', () => {
            if (this.hasChanges()) {
                this.save(true); // Synchronous save
            }
        });
    }
    
    scheduleAutoSave() {
        if (!this.isEnabled) return;
        
        // Clear existing timeout
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        
        // Schedule new save
        this.saveTimeout = setTimeout(() => {
            this.save();
        }, this.options.debounceDelay);
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        // Convert FormData to regular object
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (checkboxes)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }
    
    hasChanges() {
        const currentData = JSON.stringify(this.getFormData());
        return currentData !== this.lastSaveData;
    }
    
    async save(synchronous = false) {
        if (!this.isEnabled || this.isSaving) return;
        
        const formData = this.getFormData();
        const dataString = JSON.stringify(formData);
        
        // Don't save if no changes
        if (dataString === this.lastSaveData) {
            return;
        }
        
        this.isSaving = true;
        this.showIndicator('Saving...', 'saving');
        
        try {
            const contestId = this.form.getAttribute('data-contest-id');
            const endpoint = `/contests/${contestId}/autosave-entry`;
            
            const requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: dataString
            };
            
            let response;
            if (synchronous) {
                // Use sendBeacon for synchronous save on page unload
                const blob = new Blob([dataString], { type: 'application/json' });
                navigator.sendBeacon(endpoint, blob);
                return;
            } else {
                response = await fetch(endpoint, requestOptions);
            }
            
            if (response && response.ok) {
                this.lastSaveData = dataString;
                this.showIndicator('Saved', 'saved');
                this.storeSavedData(formData);
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Auto-save error:', error);
            this.showIndicator('Save failed', 'error');
        } finally {
            this.isSaving = false;
        }
    }
    
    showIndicator(message, type) {
        if (!this.indicator) return;
        
        this.indicator.textContent = message;
        this.indicator.className = `autosave-indicator ${type} show`;
        
        // Auto-hide after 3 seconds (except for saving state)
        if (type !== 'saving') {
            setTimeout(() => {
                this.indicator.classList.remove('show');
            }, 3000);
        }
    }
    
    storeSavedData(data) {
        // Store in localStorage for recovery
        const contestId = this.form.getAttribute('data-contest-id');
        if (contestId) {
            localStorage.setItem(`contest_entry_${contestId}`, JSON.stringify({
                data: data,
                timestamp: Date.now()
            }));
        }
    }
    
    loadSavedData() {
        // Load from localStorage if available
        const contestId = this.form.getAttribute('data-contest-id');
        if (!contestId) return;
        
        const saved = localStorage.getItem(`contest_entry_${contestId}`);
        if (saved) {
            try {
                const { data, timestamp } = JSON.parse(saved);
                
                // Only load if saved within last 24 hours
                if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
                    this.restoreFormData(data);
                    this.lastSaveData = JSON.stringify(data);
                    this.showIndicator('Draft restored', 'saved');
                }
            } catch (error) {
                console.error('Error loading saved data:', error);
            }
        }
    }
    
    restoreFormData(data) {
        // Restore form data from saved state
        Object.entries(data).forEach(([key, value]) => {
            const input = this.form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'radio' || input.type === 'checkbox') {
                    if (Array.isArray(value)) {
                        value.forEach(v => {
                            const specificInput = this.form.querySelector(`[name="${key}"][value="${v}"]`);
                            if (specificInput) specificInput.checked = true;
                        });
                    } else {
                        const specificInput = this.form.querySelector(`[name="${key}"][value="${value}"]`);
                        if (specificInput) specificInput.checked = true;
                    }
                } else {
                    input.value = value;
                }
            }
        });
    }
    
    clearSavedData() {
        // Clear saved data from localStorage
        const contestId = this.form.getAttribute('data-contest-id');
        if (contestId) {
            localStorage.removeItem(`contest_entry_${contestId}`);
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
    
    enable() {
        this.isEnabled = true;
    }
    
    disable() {
        this.isEnabled = false;
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
    }
    
    destroy() {
        this.disable();
        if (this.indicator && this.indicator.parentNode) {
            this.indicator.parentNode.removeChild(this.indicator);
        }
    }
}

// Notification system
class NotificationSystem {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.init();
    }
    
    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1060;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification-toast ${type}`;
        notification.style.pointerEvents = 'auto';
        
        const header = document.createElement('div');
        header.className = 'toast-header';
        
        const icon = this.getIcon(type);
        const title = this.getTitle(type);
        
        header.innerHTML = `
            <i class="bi ${icon} me-2"></i>
            <strong>${title}</strong>
            <button type="button" class="btn-close ms-auto" onclick="this.closest('.notification-toast').remove()"></button>
        `;
        
        const body = document.createElement('div');
        body.className = 'toast-body';
        body.textContent = message;
        
        notification.appendChild(header);
        notification.appendChild(body);
        this.container.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-remove
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }
        
        this.notifications.push(notification);
        return notification;
    }
    
    getIcon(type) {
        const icons = {
            success: 'bi-check-circle',
            error: 'bi-exclamation-triangle',
            warning: 'bi-exclamation-triangle',
            info: 'bi-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    getTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return titles[type] || titles.info;
    }
    
    clear() {
        this.notifications.forEach(notification => notification.remove());
        this.notifications = [];
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize autosave for entry forms
    const entryForm = document.getElementById('entry-form');
    if (entryForm) {
        window.autoSave = new AutoSave('entry-form');
    }
    
    // Initialize notification system
    window.notifications = new NotificationSystem();
});

// Export for use in other scripts
window.AutoSave = AutoSave;
window.NotificationSystem = NotificationSystem;
