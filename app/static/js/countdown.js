// Countdown Timer Functionality
class CountdownTimer {
    constructor(element, targetDate, options = {}) {
        this.element = element;
        this.targetDate = new Date(targetDate);
        this.options = {
            showDays: true,
            showHours: true,
            showMinutes: true,
            showSeconds: true,
            format: 'compact', // 'compact' or 'verbose'
            onExpire: null,
            updateInterval: 1000,
            ...options
        };
        this.interval = null;
        this.isExpired = false;
        
        this.init();
    }
    
    init() {
        this.update();
        this.interval = setInterval(() => this.update(), this.options.updateInterval);
    }
    
    update() {
        const now = new Date().getTime();
        const distance = this.targetDate.getTime() - now;
        
        if (distance < 0) {
            this.handleExpiration();
            return;
        }
        
        const timeUnits = this.calculateTimeUnits(distance);
        this.render(timeUnits);
    }
    
    calculateTimeUnits(distance) {
        return {
            days: Math.floor(distance / (1000 * 60 * 60 * 24)),
            hours: Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
            minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
            seconds: Math.floor((distance % (1000 * 60)) / 1000)
        };
    }
    
    render(timeUnits) {
        if (this.options.format === 'compact') {
            this.renderCompact(timeUnits);
        } else {
            this.renderVerbose(timeUnits);
        }
    }
    
    renderCompact(timeUnits) {
        const parts = [];
        
        if (this.options.showDays && timeUnits.days > 0) {
            parts.push(`${timeUnits.days}d`);
        }
        if (this.options.showHours && (timeUnits.hours > 0 || timeUnits.days > 0)) {
            parts.push(`${timeUnits.hours}h`);
        }
        if (this.options.showMinutes && (timeUnits.minutes > 0 || timeUnits.hours > 0 || timeUnits.days > 0)) {
            parts.push(`${timeUnits.minutes}m`);
        }
        if (this.options.showSeconds && timeUnits.days === 0) {
            parts.push(`${timeUnits.seconds}s`);
        }
        
        this.element.innerHTML = parts.join(' ') || '0s';
        
        // Add urgency classes
        this.updateUrgencyClass(timeUnits);
    }
    
    renderVerbose(timeUnits) {
        const parts = [];
        
        if (this.options.showDays && timeUnits.days > 0) {
            parts.push(`${timeUnits.days} day${timeUnits.days !== 1 ? 's' : ''}`);
        }
        if (this.options.showHours && (timeUnits.hours > 0 || timeUnits.days > 0)) {
            parts.push(`${timeUnits.hours} hour${timeUnits.hours !== 1 ? 's' : ''}`);
        }
        if (this.options.showMinutes && (timeUnits.minutes > 0 || timeUnits.hours > 0 || timeUnits.days > 0)) {
            parts.push(`${timeUnits.minutes} minute${timeUnits.minutes !== 1 ? 's' : ''}`);
        }
        if (this.options.showSeconds && timeUnits.days === 0) {
            parts.push(`${timeUnits.seconds} second${timeUnits.seconds !== 1 ? 's' : ''}`);
        }
        
        this.element.innerHTML = parts.join(', ') || '0 seconds';
        
        // Add urgency classes
        this.updateUrgencyClass(timeUnits);
    }
    
    updateUrgencyClass(timeUnits) {
        // Remove existing urgency classes
        this.element.classList.remove('countdown-urgent', 'countdown-critical', 'countdown-normal');
        
        const totalMinutes = timeUnits.days * 24 * 60 + timeUnits.hours * 60 + timeUnits.minutes;
        
        if (totalMinutes <= 60) {
            this.element.classList.add('countdown-critical');
        } else if (totalMinutes <= 24 * 60) {
            this.element.classList.add('countdown-urgent');
        } else {
            this.element.classList.add('countdown-normal');
        }
    }
    
    handleExpiration() {
        this.isExpired = true;
        this.element.innerHTML = 'Expired';
        this.element.classList.remove('countdown-urgent', 'countdown-critical', 'countdown-normal');
        this.element.classList.add('countdown-expired');
        
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        
        if (this.options.onExpire && typeof this.options.onExpire === 'function') {
            this.options.onExpire();
        }
    }
    
    destroy() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Initialize countdown timers on page load
document.addEventListener('DOMContentLoaded', function() {
    const countdownElements = document.querySelectorAll('[data-countdown]');
    
    countdownElements.forEach(element => {
        const targetDate = element.getAttribute('data-countdown');
        const format = element.getAttribute('data-countdown-format') || 'compact';
        const showSeconds = element.getAttribute('data-countdown-seconds') !== 'false';
        
        if (targetDate) {
            new CountdownTimer(element, targetDate, {
                format: format,
                showSeconds: showSeconds,
                onExpire: () => {
                    // Refresh page when contest expires to update UI
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            });
        }
    });
});

// Export for use in other scripts
window.CountdownTimer = CountdownTimer;
