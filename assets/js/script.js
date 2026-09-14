const header = document.querySelector(".site-header");
const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");
const form = document.getElementById("bookingForm");
const formNote = document.getElementById("formNote");

window.addEventListener("scroll", () => {
  header.classList.toggle("scrolled", window.scrollY > 25);
});

menuToggle?.addEventListener("click", () => {
  const open = navLinks.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", open ? "true" : "false");
});

document.querySelectorAll(".nav-links a").forEach(link => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
    menuToggle?.setAttribute("aria-expanded", "false");
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll(".reveal").forEach(el => observer.observe(el));

document.addEventListener("mousemove", e => {
  const glow = document.querySelector(".cursor-glow");
  if (glow) {
    glow.style.left = e.clientX + "px";
    glow.style.top = e.clientY + "px";
  }
});

form?.addEventListener("submit", e => {
  e.preventDefault();
  const data = new FormData(form);
  const name = data.get("name");
  const phone = data.get("phone");
  const service = data.get("service");
  const message = data.get("message");

  const text = `Hello REKA,%0A%0AName: ${encodeURIComponent(name)}%0APhone: ${encodeURIComponent(phone)}%0AService: ${encodeURIComponent(service)}%0ARequirement: ${encodeURIComponent(message || "Not specified")}`;
  const url = `https://wa.me/919087770472?text=${text}`;

  formNote.textContent = "Opening WhatsApp with your enquiry…";
  window.open(url, "_blank", "noopener,noreferrer");
});

document.getElementById("year").textContent = new Date().getFullYear();

// Subtle tilt on desktop for the hero machine card.
const machine = document.querySelector(".machine-card");
if (machine && window.matchMedia("(min-width: 951px)").matches) {
  document.querySelector(".hero-art")?.addEventListener("mousemove", e => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    machine.style.transform = `rotate(-4deg) rotateY(${x * 5}deg) rotateX(${y * -5}deg)`;
  });
  document.querySelector(".hero-art")?.addEventListener("mouseleave", () => {
    machine.style.transform = "rotate(-4deg)";
  });
}
