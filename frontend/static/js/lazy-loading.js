/**
 * Lazy Loading Images with Intersection Observer
 * Author: Héctor Alejandro Pérez (@halexespejo-cmd)
 */

class LazyLoader {
    constructor() {
        this.images = [];
        this.observer = null;
        this.init();
    }

    init() {
        // Check browser support
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                (entries) => this.handleIntersection(entries),
                {
                    root: null,
                    rootMargin: '50px',
                    threshold: 0.01
                }
            );
            
            // Find all lazy images
            this.images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
            this.images.forEach(img => this.observer.observe(img));
        } else {
            // Fallback: load all images
            this.loadAllImages();
        }
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                this.loadImage(img);
                this.observer.unobserve(img);
            }
        });
    }

    loadImage(img) {
        const src = img.dataset.src || img.src;
        if (src) {
            img.src = src;
            img.classList.add('loaded');
            img.removeAttribute('data-src');
        }
    }

    loadAllImages() {
        this.images.forEach(img => this.loadImage(img));
    }
}

/**
 * Lazy Load Components (defer rendering until visible)
 */
class ComponentLoader {
    constructor() {
        this.components = new Map();
        this.observer = null;
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                (entries) => this.handleComponentIntersection(entries),
                {
                    root: null,
                    rootMargin: '100px',
                    threshold: 0
                }
            );
        }
    }

    register(selector, loadFunction) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            this.components.set(el, loadFunction);
            if (this.observer) {
                this.observer.observe(el);
            }
        });
    }

    handleComponentIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const loadFunction = this.components.get(element);
                
                if (loadFunction && !element.dataset.loaded) {
                    loadFunction(element);
                    element.dataset.loaded = 'true';
                    this.observer.unobserve(element);
                }
            }
        });
    }
}

/**
 * Debounce function calls
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function calls
 */
function throttle(func, limit = 100) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Virtual Scroll for large lists
 */
class VirtualScroll {
    constructor(container, items, renderItem, itemHeight = 50) {
        this.container = container;
        this.items = items;
        this.renderItem = renderItem;
        this.itemHeight = itemHeight;
        this.visibleCount = Math.ceil(container.clientHeight / itemHeight) + 2;
        this.startIndex = 0;
        
        this.init();
    }

    init() {
        // Create scroll container
        this.scrollContainer = document.createElement('div');
        this.scrollContainer.style.height = `${this.items.length * this.itemHeight}px`;
        this.scrollContainer.style.position = 'relative';
        
        // Create viewport
        this.viewport = document.createElement('div');
        this.viewport.style.position = 'absolute';
        this.viewport.style.top = '0';
        this.viewport.style.width = '100%';
        
        this.scrollContainer.appendChild(this.viewport);
        this.container.appendChild(this.scrollContainer);
        
        // Handle scroll
        this.container.addEventListener('scroll', throttle(() => this.onScroll(), 16));
        
        // Initial render
        this.render();
    }

    onScroll() {
        const scrollTop = this.container.scrollTop;
        this.startIndex = Math.floor(scrollTop / this.itemHeight);
        this.render();
    }

    render() {
        const endIndex = this.startIndex + this.visibleCount;
        const visibleItems = this.items.slice(this.startIndex, endIndex);
        
        // Clear viewport
        this.viewport.innerHTML = '';
        this.viewport.style.transform = `translateY(${this.startIndex * this.itemHeight}px)`;
        
        // Render visible items
        visibleItems.forEach((item, index) => {
            const element = this.renderItem(item, this.startIndex + index);
            element.style.height = `${this.itemHeight}px`;
            this.viewport.appendChild(element);
        });
    }

    update(newItems) {
        this.items = newItems;
        this.scrollContainer.style.height = `${this.items.length * this.itemHeight}px`;
        this.render();
    }
}

// Initialize on load
let lazyLoader, componentLoader;

document.addEventListener('DOMContentLoaded', () => {
    lazyLoader = new LazyLoader();
    componentLoader = new ComponentLoader();
});

// Export for use in dashboard
window.LazyLoader = LazyLoader;
window.ComponentLoader = ComponentLoader;
window.VirtualScroll = VirtualScroll;
window.debounce = debounce;
window.throttle = throttle;
