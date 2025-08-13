// Le script JavaScript reste inchangé
// Initialize Lottie animations
const lottieConfigs = [
    { id: 'hero-lottie', path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' }, // Kids playing
    { id: 'about-lottie', path: 'https://assets9.lottiefiles.com/packages/lf20_DMgKk1.json' }, // Family/community
    { id: 'approach-lottie', path: 'https://assets4.lottiefiles.com/packages/lf20_khzniaya.json' }, // Learning/education
    { id: 'activities-lottie', path: 'https://assets1.lottiefiles.com/packages/lf20_q5pk6p1k.json' }, // Activities/play
    { id: 'indoor-lottie', path: 'https://assets8.lottiefiles.com/packages/lf20_fjzu4goj.json' }, // House/indoor
    { id: 'outdoor-lottie', path: 'https://assets2.lottiefiles.com/packages/lf20_khtt8lb9.json' }, // Playground/outdoor
    { id: 'communication-lottie', path: 'https://assets5.lottiefiles.com/packages/lf20_V9t630.json' }, // Communication
    { id: 'staff-lottie', path: 'https://assets7.lottiefiles.com/packages/lf20_ydo1amjm.json' }, // Teacher/staff
    { id: 'download-en-lottie', path: 'https://assets3.lottiefiles.com/packages/lf20_kuhijzpb.json' }, // Download/document
    { id: 'download-fr-lottie', path: 'https://assets3.lottiefiles.com/packages/lf20_kuhijzpb.json' }, // Download/document
    { id: 'contact-lottie', path: 'https://assets1.lottiefiles.com/packages/lf20_u25cckyh.json' } // Contact/phone
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
    if (window.scrollY > 50) {
        nav.classList.add('shadow-lg');
    } else {
        nav.classList.remove('shadow-lg');
    }
});

// Add mobile menu functionality
const mobileMenu = document.createElement('div');
mobileMenu.className = 'md:hidden';
mobileMenu.innerHTML = `
        <button id="mobile-menu-btn" class="text-lime-700 p-2">
            <i class="fas fa-bars text-xl"></i>
        </button>
        <div id="mobile-menu" class="absolute top-full left-0 w-full bg-white shadow-lg hidden">
            <div class="flex flex-col p-4 space-y-4">
                <a href="#about" class="text-lime-700 hover:text-lime-500 transition-colors">À Propos</a>
                <a href="#approach" class="text-lime-700 hover:text-lime-500 transition-colors">Notre Approche</a>
                <a href="#activities" class="text-lime-700 hover:text-lime-500 transition-colors">Activités</a>
                <a href="#environment" class="text-lime-700 hover:text-lime-500 transition-colors">Environnement</a>
                <a href="#contact" class="text-lime-700 hover:text-lime-500 transition-colors">Contact</a>
                <!-- Ajout du lien de langue dans le menu mobile -->
                <a href="{% url 'home' %}" class="text-lime-700 hover:text-lime-500 transition-colors flex items-center">
                    <img src="{% static 'images/UK.svg' %}" alt="English" class="w-5 h-5 mr-2">
                    English Version
                </a>
            </div>
        </div>
    `;

document.querySelector('nav .container > div').appendChild(mobileMenu);

document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
});

// Language dropdown functionality
function toggleLanguageDropdown() {
    const dropdown = document.getElementById('languageDropdown');
    const icon = document.getElementById('langDropdownIcon');

    dropdown.classList.toggle('opacity-0');
    dropdown.classList.toggle('scale-95');
    dropdown.classList.toggle('opacity-100');
    dropdown.classList.toggle('scale-100');

    icon.classList.toggle('rotate-180');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('languageDropdown');
    const button = event.target.closest('button');

    if (!button && dropdown.classList.contains('opacity-100')) {
        toggleLanguageDropdown();
    }
});