document.getElementById("year").textContent = new Date().getFullYear();

const navToggle = document.getElementById("navToggle");
const navMenu = document.getElementById("navMenu");

navToggle.addEventListener("click", () => {
  const open = navMenu.classList.toggle("is-open");
  navToggle.setAttribute("aria-expanded", String(open));
});

navMenu.addEventListener("click", (event) => {
  if (event.target.tagName !== "A") return;
  navMenu.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
});

const contactForm = document.getElementById("contactForm");
const formStatus = document.getElementById("formStatus");

contactForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!contactForm.reportValidity()) return;

  const submitButton = contactForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  formStatus.classList.remove("is-error");
  formStatus.textContent = "Sending your message…";

  try {
    const response = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(new FormData(contactForm))),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Your message could not be sent.");

    contactForm.reset();
    formStatus.textContent = result.message;
  } catch (error) {
    formStatus.classList.add("is-error");
    formStatus.textContent = error instanceof TypeError
      ? "Unable to reach the server. Please try again later."
      : error.message;
  } finally {
    submitButton.disabled = false;
  }
});

const revealTargets = document.querySelectorAll(".card, .hero-inner, .section-title");
revealTargets.forEach((el) => el.classList.add("reveal"));

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );
  revealTargets.forEach((el) => observer.observe(el));
} else {
  revealTargets.forEach((el) => el.classList.add("is-visible"));
}
