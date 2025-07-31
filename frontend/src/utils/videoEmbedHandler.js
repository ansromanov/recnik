// Video Embed Handler - Cleaned up code from news site
// This code handles sticky video player functionality with close button

export function initializeVideoEmbedHandler() {
    window.addEventListener("load", function () {
        // Find the video embed element
        const target = document.querySelector('.article__text [data-provider-name="pulsevideo"]');

        if (!target) {
            return; // Exit if no video embed found
        }

        // Create and add close button
        const targetClose = document.createElement('span');
        targetClose.classList.add('pulsembed_embed__close');
        targetClose.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;

        // Insert close button after the target element
        target.after(targetClose);

        // Handle close button click
        targetClose.addEventListener('click', () => {
            target.classList.remove('pulsembed_embed--sticky', 'pulsembed_embed--sticky-top');
            options.firstEnter = false;
        });

        // Intersection Observer options
        let options = {
            root: null,
            rootMargin: "100px",
            threshold: 1.0,
            firstEnter: false
        };

        // Handle intersection changes (for sticky behavior)
        function handleIntersection(entries) {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    // Video is in viewport
                    options.firstEnter = true;
                    entry.target.classList.remove('pulsembed_embed--sticky');
                } else {
                    // Video is out of viewport
                    if (options.firstEnter) {
                        entry.target.classList.add('pulsembed_embed--sticky');
                    }
                }
            });
        }

        // Create and start observer
        const observer = new IntersectionObserver(handleIntersection, options);
        observer.observe(target);

        // Handle scroll for top position adjustment
        window.addEventListener('scroll', function () {
            const header = document.querySelector('.header');

            if (header && !header.classList.contains('stuck')) {
                target.classList.add('pulsembed_embed--sticky-top');
            } else {
                target.classList.remove('pulsembed_embed--sticky-top');
            }
        });
    });
}

// CSS styles that would be needed for this functionality
export const videoEmbedStyles = `
  .pulsembed_embed--sticky {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    z-index: 1000;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .pulsembed_embed--sticky-top {
    top: 80px;
    bottom: auto;
  }

  .pulsembed_embed__close {
    position: absolute;
    top: -10px;
    right: -10px;
    width: 30px;
    height: 30px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    z-index: 1001;
  }

  .pulsembed_embed__close:hover {
    background: #f0f0f0;
  }

  .pulsembed_embed__close svg {
    width: 16px;
    height: 16px;
    color: #333;
  }
`;

// React component version (if needed)
export function VideoEmbedHandler({ children }) {
    // This would be a React version of the above functionality
    // Implementation would depend on specific requirements
    return children;
}
