// ==============================
// SIDEBAR TOGGLE (MOBILE)
// ==============================
const menuBtn = document.getElementById("mobileMenuBtn");
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

if (menuBtn && sidebar && overlay) {
    menuBtn.addEventListener("click", () => {
        sidebar.classList.toggle("-translate-x-full");
        overlay.classList.toggle("hidden");
    });

    overlay.addEventListener("click", () => {
        sidebar.classList.add("-translate-x-full");
        overlay.classList.add("hidden");
    });
}

// ==============================
// LOGOUT FUNCTION (REUSABLE)
// ==============================
function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}