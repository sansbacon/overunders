// Search and Filter functionality for contests
class ContestSearchFilter {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            searchPlaceholder: 'Search contests...',
            enableFilters: true,
            enableSort: true,
            debounceDelay: 300,
            ...options
        };
        
        this.searchTerm = '';
        this.activeFilters = new Set();
        this.sortBy = 'newest';
        this.contests = [];
        this.filteredContests = [];
        
        if (this.container) {
            this.init();
        }
    }
    
    init() {
        this.createSearchInterface();
        this.loadContests();
        this.attachEventListeners();
    }
    
    createSearchInterface() {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-filter-container';
        searchContainer.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="input-group">
                        <span class="input-group-text">
                            <i class="bi bi-search"></i>
                        </span>
                        <input type="text" 
                               class="form-control search-input" 
                               id="contest-search"
                               placeholder="${this.options.searchPlaceholder}">
                        <button class="btn btn-outline-secondary" 
                                type="button" 
                                id="clear-search"
                                title="Clear search">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="col-md-3">
                    <select class="form-select" id="contest-sort">
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="name-asc">Name A-Z</option>
                        <option value="name-desc">Name Z-A</option>
                        <option value="deadline">By Deadline</option>
                        <option value="entries">Most Entries</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <div class="dropdown">
                        <button class="btn btn-outline-primary dropdown-toggle w-100" 
                                type="button" 
                                id="filter-dropdown"
                                data-bs-toggle="dropdown">
                            <i class="bi bi-funnel"></i> Filters
                        </button>
                        <ul class="dropdown-menu" id="filter-menu">
                            <li>
                                <label class="dropdown-item">
                                    <input type="checkbox" value="open" class="me-2">
                                    Open for Entry
                                </label>
                            </li>
                            <li>
                                <label class="dropdown-item">
                                    <input type="checkbox" value="locked" class="me-2">
                                    Locked
                                </label>
                            </li>
                            <li>
                                <label class="dropdown-item">
                                    <input type="checkbox" value="my-contests" class="me-2">
                                    My Contests
                                </label>
                            </li>
                            <li>
                                <label class="dropdown-item">
                                    <input type="checkbox" value="entered" class="me-2">
                                    I've Entered
                                </label>
                            </li>
                            <li>
                                <label class="dropdown-item">
                                    <input type="checkbox" value="not-entered" class="me-2">
                                    Not Entered
                                </label>
                            </li>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <label class="dropdown-item">
                                    <input type="checkbox" value="has-results" class="me-2">
                                    Has Results
                                </label>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="filter-tags mt-2" id="active-filters"></div>
            <div class="search-stats mt-2" id="search-stats"></div>
        `;
        
        // Insert before the contests container
        this.container.parentNode.insertBefore(searchContainer, this.container);
        this.searchContainer = searchContainer;
    }
    
    attachEventListeners() {
        // Search input
        const searchInput = document.getElementById('contest-search');
        const clearButton = document.getElementById('clear-search');
        
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchTerm = e.target.value.toLowerCase().trim();
                this.filterAndSort();
            }, this.options.debounceDelay);
        });
        
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            this.searchTerm = '';
            this.filterAndSort();
        });
        
        // Sort dropdown
        const sortSelect = document.getElementById('contest-sort');
        sortSelect.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.filterAndSort();
        });
        
        // Filter checkboxes
        const filterCheckboxes = document.querySelectorAll('#filter-menu input[type="checkbox"]');
        filterCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.activeFilters.add(e.target.value);
                } else {
                    this.activeFilters.delete(e.target.value);
                }
                this.updateFilterTags();
                this.filterAndSort();
            });
        });
        
        // Prevent dropdown from closing when clicking checkboxes
        document.getElementById('filter-menu').addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    loadContests() {
        // Extract contest data from existing DOM elements
        const contestCards = this.container.querySelectorAll('.contest-card, .card');
        this.contests = Array.from(contestCards).map(card => {
            return {
                element: card,
                name: this.extractText(card, '.card-title, h5, h4'),
                description: this.extractText(card, '.card-text, p'),
                creator: this.extractText(card, '.creator, .text-muted'),
                isLocked: card.querySelector('.badge')?.textContent.toLowerCase().includes('locked') || false,
                isOpen: !card.querySelector('.badge')?.textContent.toLowerCase().includes('locked'),
                entryCount: this.extractNumber(card, '.entry-count, .badge'),
                deadline: this.extractDate(card, '.deadline, .lock-time'),
                createdAt: this.extractDate(card, '.created-at'),
                isMyContest: card.querySelector('[data-my-contest]') !== null,
                hasEntered: card.querySelector('[data-entered]') !== null,
                hasResults: card.querySelector('[data-has-results]') !== null
            };
        });
        
        this.filteredContests = [...this.contests];
        this.updateStats();
    }
    
    extractText(element, selector) {
        const target = element.querySelector(selector);
        return target ? target.textContent.trim() : '';
    }
    
    extractNumber(element, selector) {
        const target = element.querySelector(selector);
        if (!target) return 0;
        const match = target.textContent.match(/\d+/);
        return match ? parseInt(match[0]) : 0;
    }
    
    extractDate(element, selector) {
        const target = element.querySelector(selector);
        if (!target) return null;
        
        const dateStr = target.textContent.trim();
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? null : date;
    }
    
    filterAndSort() {
        // Apply search filter
        let filtered = this.contests.filter(contest => {
            if (this.searchTerm) {
                const searchableText = `${contest.name} ${contest.description} ${contest.creator}`.toLowerCase();
                if (!searchableText.includes(this.searchTerm)) {
                    return false;
                }
            }
            return true;
        });
        
        // Apply active filters
        filtered = filtered.filter(contest => {
            for (let filter of this.activeFilters) {
                switch (filter) {
                    case 'open':
                        if (!contest.isOpen) return false;
                        break;
                    case 'locked':
                        if (!contest.isLocked) return false;
                        break;
                    case 'my-contests':
                        if (!contest.isMyContest) return false;
                        break;
                    case 'entered':
                        if (!contest.hasEntered) return false;
                        break;
                    case 'not-entered':
                        if (contest.hasEntered) return false;
                        break;
                    case 'has-results':
                        if (!contest.hasResults) return false;
                        break;
                }
            }
            return true;
        });
        
        // Apply sorting
        filtered.sort((a, b) => {
            switch (this.sortBy) {
                case 'newest':
                    return (b.createdAt || 0) - (a.createdAt || 0);
                case 'oldest':
                    return (a.createdAt || 0) - (b.createdAt || 0);
                case 'name-asc':
                    return a.name.localeCompare(b.name);
                case 'name-desc':
                    return b.name.localeCompare(a.name);
                case 'deadline':
                    if (!a.deadline && !b.deadline) return 0;
                    if (!a.deadline) return 1;
                    if (!b.deadline) return -1;
                    return a.deadline - b.deadline;
                case 'entries':
                    return b.entryCount - a.entryCount;
                default:
                    return 0;
            }
        });
        
        this.filteredContests = filtered;
        this.updateDisplay();
        this.updateStats();
    }
    
    updateDisplay() {
        // Hide all contests first
        this.contests.forEach(contest => {
            contest.element.style.display = 'none';
        });
        
        // Show filtered contests
        this.filteredContests.forEach((contest, index) => {
            contest.element.style.display = 'block';
            contest.element.style.order = index;
        });
        
        // Show no results message if needed
        this.showNoResultsMessage();
    }
    
    showNoResultsMessage() {
        let noResultsMsg = document.getElementById('no-results-message');
        
        if (this.filteredContests.length === 0) {
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.id = 'no-results-message';
                noResultsMsg.className = 'text-center py-5';
                noResultsMsg.innerHTML = `
                    <div class="text-muted">
                        <i class="bi bi-search" style="font-size: 3rem;"></i>
                        <h4 class="mt-3">No contests found</h4>
                        <p>Try adjusting your search terms or filters.</p>
                        <button class="btn btn-outline-primary" onclick="window.contestSearch.clearAll()">
                            Clear All Filters
                        </button>
                    </div>
                `;
                this.container.appendChild(noResultsMsg);
            }
            noResultsMsg.style.display = 'block';
        } else if (noResultsMsg) {
            noResultsMsg.style.display = 'none';
        }
    }
    
    updateFilterTags() {
        const tagsContainer = document.getElementById('active-filters');
        tagsContainer.innerHTML = '';
        
        this.activeFilters.forEach(filter => {
            const tag = document.createElement('span');
            tag.className = 'filter-tag';
            tag.innerHTML = `
                ${this.getFilterLabel(filter)}
                <span class="remove" onclick="window.contestSearch.removeFilter('${filter}')">&times;</span>
            `;
            tagsContainer.appendChild(tag);
        });
    }
    
    getFilterLabel(filter) {
        const labels = {
            'open': 'Open for Entry',
            'locked': 'Locked',
            'my-contests': 'My Contests',
            'entered': "I've Entered",
            'not-entered': 'Not Entered',
            'has-results': 'Has Results'
        };
        return labels[filter] || filter;
    }
    
    updateStats() {
        const statsContainer = document.getElementById('search-stats');
        const total = this.contests.length;
        const filtered = this.filteredContests.length;
        
        if (filtered !== total || this.searchTerm || this.activeFilters.size > 0) {
            statsContainer.innerHTML = `
                <small class="text-muted">
                    Showing ${filtered} of ${total} contests
                </small>
            `;
            statsContainer.style.display = 'block';
        } else {
            statsContainer.style.display = 'none';
        }
    }
    
    removeFilter(filter) {
        this.activeFilters.delete(filter);
        
        // Update checkbox state
        const checkbox = document.querySelector(`#filter-menu input[value="${filter}"]`);
        if (checkbox) {
            checkbox.checked = false;
        }
        
        this.updateFilterTags();
        this.filterAndSort();
    }
    
    clearAll() {
        // Clear search
        const searchInput = document.getElementById('contest-search');
        if (searchInput) {
            searchInput.value = '';
        }
        this.searchTerm = '';
        
        // Clear filters
        this.activeFilters.clear();
        const checkboxes = document.querySelectorAll('#filter-menu input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        
        // Reset sort
        const sortSelect = document.getElementById('contest-sort');
        if (sortSelect) {
            sortSelect.value = 'newest';
        }
        this.sortBy = 'newest';
        
        this.updateFilterTags();
        this.filterAndSort();
    }
    
    refresh() {
        // Reload contests from DOM (useful after AJAX updates)
        this.loadContests();
        this.filterAndSort();
    }
}

// Initialize search and filter on page load
document.addEventListener('DOMContentLoaded', function() {
    // Look for contest containers
    const contestContainers = [
        'contests-container',
        'contest-list',
        'contests-grid'
    ];
    
    for (let containerId of contestContainers) {
        const container = document.getElementById(containerId);
        if (container) {
            window.contestSearch = new ContestSearchFilter(containerId);
            break;
        }
    }
    
    // Also check for generic containers with contest cards
    if (!window.contestSearch) {
        const containers = document.querySelectorAll('.container, .row');
        for (let container of containers) {
            if (container.querySelector('.contest-card, .card')) {
                container.id = container.id || 'auto-contest-container';
                window.contestSearch = new ContestSearchFilter(container.id);
                break;
            }
        }
    }
});

// Export for use in other scripts
window.ContestSearchFilter = ContestSearchFilter;
