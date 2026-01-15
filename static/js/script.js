document.addEventListener('DOMContentLoaded', function () {

    // 1. Mobile Menu Toggle
    const menuBtn = document.querySelector('.menu-btn');
    const menuItems = document.querySelector('#MenuItems');

    if (menuBtn && menuItems) {
        menuBtn.addEventListener('click', function () {
            menuItems.classList.toggle('active');
        });
    }

    // 2. Login Page Tab Switcher
    const tabs = document.querySelectorAll('.login-tab');
    const forms = document.querySelectorAll('.login-form');

    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function () {
                const target = this.getAttribute('data-tab');
                tabs.forEach(t => t.classList.remove('active'));
                forms.forEach(f => f.classList.remove('active'));
                this.classList.add('active');
                const targetForm = document.getElementById(target + '-form');
                if (targetForm) targetForm.classList.add('active');
            });
        });
    }

    // 3. Category Card Hover Effects
    // We only handle the image scale here; CSS handles text visibility for About/Home
    const categoryCards = document.querySelectorAll('.category-card');

    categoryCards.forEach(card => {
        const img = card.querySelector('img');

        if (img) {
            card.addEventListener('mouseenter', function () {
                img.style.transform = 'scale(1.1)';
            });

            card.addEventListener('mouseleave', function () {
                img.style.transform = 'scale(1)';
            });
        }
    });

    // 4. Specific Login Validation
    const loginForms = document.querySelectorAll('.login-form');
    loginForms.forEach(form => {
        form.addEventListener('submit', function (event) {
            // Find inputs specifically within the submitted form
            const emailInput = form.querySelector('input[type="email"]');
            const passwordInput = form.querySelector('input[type="password"]');

            if (emailInput && !emailInput.value.trim() || passwordInput && !passwordInput.value.trim()) {
                event.preventDefault();
                alert('Both email and password are required!');
            }
        });
    });
});

// 5. Countdown Timer for Deals
function updateCountdown() {
    const hoursElement = document.getElementById('hours');
    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');

    // Safety check: only run if the timer exists on the current page
    if (!hoursElement || !minutesElement || !secondsElement) return;

    const now = new Date();
    const endOfDay = new Date();
    endOfDay.setHours(23, 59, 59, 0);

    const diff = endOfDay - now;

    if (diff > 0) {
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        hoursElement.textContent = hours.toString().padStart(2, '0');
        minutesElement.textContent = minutes.toString().padStart(2, '0');
        secondsElement.textContent = seconds.toString().padStart(2, '0');
    }
}

// Initialize Timer
setInterval(updateCountdown, 1000);
updateCountdown();