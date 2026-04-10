// News Timeline JavaScript
class TimelineManager {
    constructor() {
        this.timeline = null;
        this.currentEvents = [];
        this.currentFilters = {
            startDate: null,
            endDate: null,
            eventTypes: ['news', 'positive_news', 'alert'],
            importanceMin: 1,
            searchQuery: null
        };
        this.isLoading = false;
        this.init();
    }

    init() {
        // Initialize importance range display
        const importanceRange = document.getElementById('importanceRange');
        const importanceValue = document.getElementById('importanceValue');
        if (importanceRange) {
            importanceRange.addEventListener('input', function() {
                importanceValue.textContent = this.value;
            });
        }

        // Load timeline and stats
        this.loadTimeline();
        this.loadStats();

        // Set up event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh button
        window.refreshTimeline = () => this.loadTimeline();

        // Search input Enter key
        const searchInput = document.getElementById('searchQuery');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchEvents();
                }
            });
        }
    }

    async loadTimeline(filters = null) {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading(true);

        try {
            // Merge filters
            const effectiveFilters = filters || this.currentFilters;

            // Build query parameters
            const params = new URLSearchParams();

            if (effectiveFilters.startDate) {
                params.append('start_date', effectiveFilters.startDate);
            }
            if (effectiveFilters.endDate) {
                params.append('end_date', effectiveFilters.endDate);
            }
            if (effectiveFilters.eventTypes && effectiveFilters.eventTypes.length > 0) {
                effectiveFilters.eventTypes.forEach(type => {
                    params.append('event_types', type);
                });
            }
            if (effectiveFilters.importanceMin) {
                params.append('importance_min', effectiveFilters.importanceMin);
            }
            if (effectiveFilters.searchQuery) {
                params.append('search', effectiveFilters.searchQuery);
            }

            params.append('page', '1');
            params.append('limit', '100');

            // Make API request
            const response = await axios.get(`/api/news/timeline?${params.toString()}`);
            this.currentEvents = response.data.events;

            // Render timeline
            this.renderTimeline();

        } catch (error) {
            console.error('Failed to load timeline:', error);
            this.showError('Failed to load timeline events. Please try again.');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    renderTimeline() {
        const container = document.getElementById('timeline');
        if (!container) return;

        // Clear existing timeline
        if (this.timeline) {
            this.timeline.destroy();
        }

        // Prepare items for vis.js
        const items = new vis.DataSet(
            this.currentEvents.map(event => ({
                id: event.id,
                content: this.getEventContent(event),
                start: new Date(event.event_date),
                end: new Date(event.event_date),
                type: 'box',
                className: `event-${event.event_type}`,
                event: event
            }))
        );

        // Configuration options
        const options = {
            height: '100%',
            min: this.currentFilters.startDate ? new Date(this.currentFilters.startDate) : null,
            max: this.currentFilters.endDate ? new Date(this.currentFilters.endDate) : null,
            zoomMin: 1000 * 60 * 60 * 24, // 1 day in milliseconds
            zoomMax: 1000 * 60 * 60 * 24 * 365 * 10, // 10 years
            orientation: 'top',
            showCurrentTime: false,
            tooltip: {
                followMouse: true,
                overflowMethod: 'cap'
            },
            stack: false,
            verticalScroll: true,
            horizontalScroll: true
        };

        // Create timeline
        this.timeline = new vis.Timeline(container, items, options);

        // Add click event
        this.timeline.on('click', (properties) => {
            if (properties.item) {
                const eventId = properties.item;
                const event = this.currentEvents.find(e => e.id === eventId);
                if (event) {
                    this.showEventDetail(event);
                }
            }
        });

        // Add double-click event for zoom
        this.timeline.on('doubleClick', (properties) => {
            if (properties.item) {
                const eventId = properties.item;
                const event = this.currentEvents.find(e => e.id === eventId);
                if (event) {
                    const eventDate = new Date(event.event_date);
                    const range = 1000 * 60 * 60 * 24 * 7; // 1 week
                    this.timeline.setWindow(eventDate.getTime() - range, eventDate.getTime() + range);
                }
            }
        });
    }

    getEventContent(event) {
        const importanceStars = '★'.repeat(event.importance) + '☆'.repeat(5 - event.importance);

        return `
            <div class="timeline-event">
                <div class="fw-bold">${event.title}</div>
                <div class="small text-muted">
                    ${new Date(event.event_date).toLocaleDateString()}
                    <span class="ms-2">${importanceStars}</span>
                </div>
            </div>
        `;
    }

    showEventDetail(event) {
        const detailDiv = document.getElementById('eventDetail');
        const titleEl = document.getElementById('eventTitle');
        const typeBadgeEl = document.getElementById('eventTypeBadge');
        const dateEl = document.getElementById('eventDate');
        const importanceEl = document.getElementById('eventImportance');
        const descriptionEl = document.getElementById('eventDescription');
        const tagsEl = document.getElementById('eventTags');
        const keyPointsEl = document.getElementById('eventKeyPoints');

        if (!detailDiv) return;

        // Update content
        titleEl.textContent = event.title;
        typeBadgeEl.textContent = event.event_type.replace('_', ' ').toUpperCase();
        typeBadgeEl.className = `event-type-badge event-type-${event.event_type}`;
        dateEl.textContent = new Date(event.event_date).toLocaleString();

        const importanceStars = '★'.repeat(event.importance) + '☆'.repeat(5 - event.importance);
        importanceEl.innerHTML = `<span class="importance-star">${importanceStars}</span>`;

        descriptionEl.textContent = event.description || 'No description available.';

        // Tags
        const tags = event.metadata?.tags || [];
        if (tags.length > 0) {
            tagsEl.innerHTML = `
                <strong>Tags:</strong>
                ${tags.map(tag => `<span class="badge bg-secondary me-1">${tag}</span>`).join('')}
            `;
        } else {
            tagsEl.innerHTML = '';
        }

        // Key points
        const keyPoints = event.metadata?.key_points || [];
        if (keyPoints.length > 0) {
            keyPointsEl.innerHTML = `
                <strong>Key Points:</strong>
                <ul class="mt-2">
                    ${keyPoints.map(point => `<li>${point}</li>`).join('')}
                </ul>
            `;
        } else {
            keyPointsEl.innerHTML = '';
        }

        // Show detail panel
        detailDiv.style.display = 'block';
    }

    hideEventDetail() {
        const detailDiv = document.getElementById('eventDetail');
        if (detailDiv) {
            detailDiv.style.display = 'none';
        }
    }

    async loadStats() {
        try {
            const response = await axios.get('/api/news/timeline/stats');
            this.renderStats(response.data);
        } catch (error) {
            console.error('Failed to load stats:', error);
            this.renderStats(null);
        }
    }

    renderStats(data) {
        const statsContent = document.getElementById('statsContent');
        if (!statsContent) return;

        if (!data) {
            statsContent.innerHTML = '<p class="text-danger">Failed to load statistics</p>';
            return;
        }

        let html = `
            <div class="row text-center">
                <div class="col-md-4 mb-3">
                    <div class="card bg-light">
                        <div class="card-body">
                            <h3 class="display-6">${data.total_events}</h3>
                            <p class="text-muted mb-0">Total Events</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="card bg-light">
                        <div class="card-body">
                            <h3 class="display-6">${data.average_importance.toFixed(1)}</h3>
                            <p class="text-muted mb-0">Avg Importance</p>
                        </div>
                    </div>
                </div>
        `;

        // Event types breakdown
        if (data.events_by_type) {
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card bg-light">
                        <div class="card-body">
                            <h3 class="display-6">${Object.keys(data.events_by_type).length}</h3>
                            <p class="text-muted mb-0">Event Types</p>
                        </div>
                    </div>
                </div>
            `;
        }

        html += `</div>`;

        // Event type distribution
        if (data.events_by_type) {
            html += `<div class="mt-3"><strong>Event Distribution:</strong>`;
            for (const [type, count] of Object.entries(data.events_by_type)) {
                const percentage = (count / data.total_events * 100).toFixed(1);
                html += `
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <span class="event-type-badge event-type-${type}">${type}</span>
                        <span>${count} (${percentage}%)</span>
                    </div>
                    <div class="progress mt-1" style="height: 5px;">
                        <div class="progress-bar" role="progressbar" style="width: ${percentage}%"></div>
                    </div>
                `;
            }
            html += `</div>`;
        }

        statsContent.innerHTML = html;
    }

    applyFilters() {
        // Get date values
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');

        this.currentFilters.startDate = startDateInput.value || null;
        this.currentFilters.endDate = endDateInput.value || null;

        // Get selected event types
        const eventTypes = [];
        document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
            eventTypes.push(checkbox.value);
        });
        this.currentFilters.eventTypes = eventTypes;

        // Get importance filter
        const importanceRange = document.getElementById('importanceRange');
        this.currentFilters.importanceMin = importanceRange ? parseInt(importanceRange.value) : 1;

        // Get search query
        const searchInput = document.getElementById('searchQuery');
        this.currentFilters.searchQuery = searchInput.value.trim() || null;

        // Reload timeline with new filters
        this.loadTimeline();
    }

    searchEvents() {
        const searchInput = document.getElementById('searchQuery');
        this.currentFilters.searchQuery = searchInput.value.trim() || null;
        this.loadTimeline();
    }

    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const timelineContainer = document.getElementById('timeline');

        if (loadingIndicator && timelineContainer) {
            if (show) {
                loadingIndicator.style.display = 'flex';
                timelineContainer.style.opacity = '0.5';
            } else {
                loadingIndicator.style.display = 'none';
                timelineContainer.style.opacity = '1';
            }
        }
    }

    showError(message) {
        // Simple error display
        alert(message);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.timelineManager = new TimelineManager();
});

// Global functions for HTML onclick handlers
window.applyFilters = function() {
    if (window.timelineManager) {
        window.timelineManager.applyFilters();
    }
};

window.searchEvents = function() {
    if (window.timelineManager) {
        window.timelineManager.searchEvents();
    }
};

window.hideEventDetail = function() {
    if (window.timelineManager) {
        window.timelineManager.hideEventDetail();
    }
};