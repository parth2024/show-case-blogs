// 

document.addEventListener("DOMContentLoaded", function () {

  const navbar = document.getElementById("navbar");
  const heroSection = document.getElementById("hero");
  const toTopButton = document.getElementById("toTopButton");


  // Logique unifiée pour le menu full-screen et mobile (NOUVEAU)
  const menuButton = document.getElementById("menu-button");
  const fullscreenNav = document.getElementById("fullscreen-nav");
  const fullscreenCloseButton = document.getElementById(
    "fullscreen-close-button"
  );

  if (menuButton && fullscreenNav && fullscreenCloseButton) {
    menuButton.addEventListener("click", () => {
      fullscreenNav.classList.remove("hidden");
      document.body.style.overflow = "hidden"; // Empêche le défilement de la page
    });

    fullscreenCloseButton.addEventListener("click", () => {
      fullscreenNav.classList.add("hidden");
      document.body.style.overflow = "auto"; // Restaure le défilement
    });
  }



  // Dynamic navbar on scroll
  if (navbar && heroSection) {
    const heroHeight = heroSection.offsetHeight;

    window.addEventListener("scroll", () => {
      if (window.scrollY > heroHeight * 0.8) {
        navbar.classList.add("bg-violet-900", "shadow-lg");
        navbar.classList.remove("absolute", "py-6");
        navbar.classList.add("fixed");
      } else {
        navbar.classList.remove("bg-violet-900", "shadow-lg");
        navbar.classList.add("absolute");
        navbar.classList.remove("fixed");
      }
    });
  }

  // Back to top button logic
  if (toTopButton) {
    // const heroHeight = heroSection.offsetTop + heroSection.offsetHeight;
    const scrollPoint = 300;
    window.addEventListener("scroll", () => {
      if (window.scrollY > scrollPoint) {

        toTopButton.classList.remove("invisible", "pointer-events-none");

      } else {

        toTopButton.classList.add("invisible", "pointer-events-none");

      }
    });
  }

  // Activités Slider
  const slider = document.getElementById("activities-slider");
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");

  if (slider && prevBtn && nextBtn) {
    // Fonction pour défiler d'une seule carte
    const scrollByCard = (direction) => {
      // Calcule la largeur d'une carte, y compris les marges
      const card = slider.querySelector('.snap-start');
      if (card) {
        const cardWidth = card.offsetWidth;
        const scrollAmount = direction * cardWidth;
        slider.scrollBy({
          left: scrollAmount,
          behavior: 'smooth',
        });
      }
    };

    prevBtn.addEventListener("click", () => {
      scrollByCard(-1); // Défilement vers la gauche
    });

    nextBtn.addEventListener("click", () => {
      scrollByCard(1); // Défilement vers la droite
    });
  }

  // Blog Slider
  const blogSlider = document.getElementById("blog-slider");
  const prevBlogBtn = document.getElementById("prev-blog-btn");
  const nextBlogBtn = document.getElementById("next-blog-btn");

  if (blogSlider && prevBlogBtn && nextBlogBtn) {
    const scrollByBlogCard = (direction) => {
      const card = blogSlider.querySelector('.snap-start');
      if (card) {
        const cardWidth = card.offsetWidth;
        const scrollAmount = direction * cardWidth;
        blogSlider.scrollBy({ left: scrollAmount, behavior: "smooth" });
      }
    };
    prevBlogBtn.addEventListener("click", () => scrollByBlogCard(-1));
    nextBlogBtn.addEventListener("click", () => scrollByBlogCard(1));
  }
});