document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const menuBtn = document.querySelector('.menu-btn');
    const menuItems = document.querySelector('#MenuItems');
    
    if (menuBtn && menuItems) {
        menuBtn.addEventListener('click', function() {
            menuItems.classList.toggle('active');
        });
    }
    
    // Category Card Hover Effects
    const categoryCards = document.querySelectorAll('.category-card');
    
    categoryCards.forEach(card => {
        const img = card.querySelector('img');
        const info = card.querySelector('.category-info');
        
        card.addEventListener('mouseenter', function() {
            img.style.transform = 'scale(1.1)';
            info.style.transform = 'translateY(0)';
        });
        
        card.addEventListener('mouseleave', function() {
            img.style.transform = 'scale(1)';
            info.style.transform = 'translateY(100%)';
        });
    });
});



// Countdown Timer for Deals
function updateCountdown() {
    const now = new Date();
    const endOfDay = new Date();
    endOfDay.setHours(23, 59, 59, 0);
    
    const diff = endOfDay - now;
    
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    document.getElementById('hours').textContent = Math.floor(hours).toString().padStart(2, '0');
    document.getElementById('minutes').textContent = Math.floor(minutes).toString().padStart(2, '0');
    document.getElementById('seconds').textContent = Math.floor(seconds).toString().padStart(2, '0');
}

// Update every second
setInterval(updateCountdown, 1000);
updateCountdown(); // Initial call