// Initialize Lottie animations
const lottieConfigs = [
    { id: 'hero-lottie', path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' },
    { id: 'about-lottie', path: 'https://assets9.lottiefiles.com/packages/lf20_DMgKk1.json' },
    { id: 'approach-lottie', path: 'https://assets4.lottiefiles.com/packages/lf20_khzniaya.json' },
    { id: 'activities-lottie', path: 'https://assets1.lottiefiles.com/packages/lf20_q5pk6p1k.json' },
    { id: 'indoor-lottie', path: 'https://assets8.lottiefiles.com/packages/lf20_fjzu4goj.json' },
    { id: 'outdoor-lottie', path: 'https://assets2.lottiefiles.com/packages/lf20_khtt8lb9.json' },
    { id: 'communication-lottie', path: 'https://assets5.lottiefiles.com/packages/lf20_V9t630.json' },
    { id: 'staff-lottie', path: 'https://assets7.lottiefiles.com/packages/lf20_ydo1amjm.json' },
    { id: 'download-en-lottie', path: 'https://assets3.lottiefiles.com/packages/lf20_kuhijzpb.json' },
    { id: 'download-fr-lottie', path: 'https://assets3.lottiefiles.com/packages/lf20_kuhijzpb.json' },
    { id: 'contact-lottie', path: 'https://assets1.lottiefiles.com/packages/lf20_u25cckyh.json' }
];

// Load Lottie animations
lottieConfigs.forEach(config => {
    const element = document.getElementById(config.id);
    if (element) {
        lottie.loadAnimation({
            container: element,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: config.path
        });
    }
});

// Scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animated');
        }
    });
}, observerOptions);

// Observe all elements with animate-on-scroll class
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(el => observer.observe(el));

    // Initialize mobile menu functionality
    initializeMobileMenu();
});

// Initialize mobile menu functionality
function initializeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
            
            // Animate hamburger icon
            const lines = mobileMenuBtn.querySelectorAll('path');
            if (mobileMenu.classList.contains('hidden')) {
                // Reset to hamburger
                lines[0].setAttribute('d', 'M4 6h16');
                lines[1].setAttribute('d', 'M4 12h16');
                lines[2].setAttribute('d', 'M4 18h16');
            } else {
                // Transform to X
                lines[0].setAttribute('d', 'M6 18L18 6');
                lines[1].setAttribute('d', 'M6 6l12 12');
                lines[2].setAttribute('d', 'M6 6l12 12');
            }
        });

        // Close mobile menu when clicking on links
        const mobileLinks = mobileMenu.querySelectorAll('a[href^="#"]');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.add('hidden');
                // Reset hamburger icon
                const lines = mobileMenuBtn.querySelectorAll('path');
                lines[0].setAttribute('d', 'M4 6h16');
                lines[1].setAttribute('d', 'M4 12h16');
                lines[2].setAttribute('d', 'M4 18h16');
            });
        });
    }
}

// Toggle mobile language options
function toggleMobileLanguage() {
    const mobileLanguageOptions = document.getElementById('mobile-language-options');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileLanguageOptions && mobileMenu) {
        if (mobileMenu.classList.contains('hidden')) {
            mobileMenu.classList.remove('hidden');
        }
        
        if (mobileLanguageOptions.style.display === 'none') {
            mobileLanguageOptions.style.display = 'block';
        } else {
            mobileLanguageOptions.style.display = 'none';
        }
    }
}

// Desktop language dropdown functionality
function toggleLanguageDropdown() {
    const dropdown = document.getElementById('languageDropdown');
    const icon = document.getElementById('langDropdownIcon');

    if (dropdown && icon) {
        dropdown.classList.toggle('opacity-0');
        dropdown.classList.toggle('scale-95');
        dropdown.classList.toggle('opacity-100');
        dropdown.classList.toggle('scale-100');

        icon.classList.toggle('rotate-180');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('languageDropdown');
    const button = event.target.closest('button[onclick="toggleLanguageDropdown()"]');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileLanguageBtn = event.target.closest('button[onclick="toggleMobileLanguage()"]');

    // Close language dropdown if clicking outside
    if (!button && dropdown && dropdown.classList.contains('opacity-100')) {
        toggleLanguageDropdown();
    }

    // Close mobile menu if clicking outside
    if (!mobileMenuBtn?.contains(event.target) && !mobileMenu?.contains(event.target) && !mobileLanguageBtn) {
        if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
            mobileMenu.classList.add('hidden');
            // Reset hamburger icon
            const lines = mobileMenuBtn?.querySelectorAll('path');
            if (lines) {
                lines[0]?.setAttribute('d', 'M4 6h16');
                lines[1]?.setAttribute('d', 'M4 12h16');
                lines[2]?.setAttribute('d', 'M4 18h16');
            }
        }
    }
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add scroll effect to navigation
window.addEventListener('scroll', () => {
    const nav = document.querySelector('nav');
    if (nav) {
        if (window.scrollY > 50) {
            nav.classList.add('shadow-lg');
        } else {
            nav.classList.remove('shadow-lg');
        }
    }
});