// script.js

// Function to show a confirmation before form submission
function confirmSubmission() {
    return confirm("Are you sure you want to submit?");
}

// Function to dynamically change the page title
document.addEventListener("DOMContentLoaded", function () {
    const pageTitle = document.querySelector('h1');
    if (pageTitle) {
        document.title = pageTitle.textContent + " - NLP Resume Matching";
    }
});

// Smooth scroll for internal links (only for anchors starting with "#")
document.querySelectorAll('nav a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        // Check if the link is an internal anchor (starts with "#")
        if (href && href.startsWith('#')) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        }
    });
});

