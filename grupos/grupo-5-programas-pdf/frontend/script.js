const sectionLinks = document.querySelectorAll(".nav-secciones a");
const sections = document.querySelectorAll(".area-trabajo .seccion");

sectionLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    const sectionId = link.getAttribute("href").slice(1);

    sectionLinks.forEach((item) => {
      item.classList.toggle("activa", item === link);
      item.removeAttribute("aria-current");
    });
    link.setAttribute("aria-current", "page");

    sections.forEach((section) => {
      section.classList.toggle("activa", section.id === sectionId);
    });
  });
});
