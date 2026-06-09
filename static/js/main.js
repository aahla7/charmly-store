// Update cart count from localStorage
function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('charmly_cart')) || [];
    const count = cart.reduce((sum, item) => sum + item.qty, 0);
    document.querySelectorAll('.cart-count').forEach(el => el.textContent = count);
}

// Add item to cart
function addToCart(id, name, price, emoji, image) {
    let cart = JSON.parse(localStorage.getItem('charmly_cart')) || [];
    const existing = cart.find(item => item.id === id);
    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({ id, name, price, emoji: emoji || '🔑', image: image || '', qty: 1 });
    }
    localStorage.setItem('charmly_cart', JSON.stringify(cart));
    updateCartCount();

    // Visual feedback
    const btn = event.target;
    btn.textContent = '✓';
    btn.style.background = '#06D6A0';
    setTimeout(() => {
        btn.textContent = '+';
        btn.style.background = '';
    }, 1200);
}

// Hamburger menu toggle
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
if (hamburger) {
    hamburger.addEventListener('click', () => {
        mobileMenu.classList.toggle('open');
    });
}

// Run on every page load
updateCartCount();