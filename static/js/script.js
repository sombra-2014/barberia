document.addEventListener('DOMContentLoaded', function() {
    // --- JavaScript para el menú responsivo ---
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');

    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
        });

        // Cierra el menú si se hace clic fuera de él en móviles
        document.addEventListener('click', function(event) {
            if (!mainNav.contains(event.target) && !menuToggle.contains(event.target) && mainNav.classList.contains('active')) {
                mainNav.classList.remove('active');
            }
        });
    }

    // --- JavaScript para el scroll suave en los anclajes (opcional) ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });

            // Cierra el menú responsivo si se hace clic en un enlace
            if (mainNav.classList.contains('active')) {
                mainNav.classList.remove('active');
            }
        });
    });

    // --- JavaScript para el "slider" de testimonios (simple, si no usas librerías) ---
    // Si tienes un slider real, integrarías aquí la librería correspondiente (ej. Swiper, Owl Carousel)
    // Este es un ejemplo muy básico si solo quieres que se vean bien uno al lado del otro
    // y permitir el scroll en móviles.
    const testimonialsContainer = document.querySelector('.testimonials-slider');
    if (testimonialsContainer) {
        // Puedes añadir aquí lógica para flechas de navegación o puntos si lo deseas
        // Por ahora, simplemente se basa en el CSS con overflow-x: auto y scroll-snap-type.
    }
});