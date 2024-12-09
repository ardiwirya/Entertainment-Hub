document.addEventListener("DOMContentLoaded", function () {
  // Contoh: Validasi form
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const password = form.querySelector('input[type="password"]');
      if (password && password.value.length < 6) {
        e.preventDefault();
        alert("Password minimal 6 karakter");
      }
    });
  });

  // Animasi sederhana
  const entertainmentItems = document.querySelectorAll(".entertainment-item");
  entertainmentItems.forEach((item) => {
    item.addEventListener("mouseover", function () {
      this.style.transform = "scale(1.05)";
    });
    item.addEventListener("mouseout", function () {
      this.style.transform = "scale(1)";
    });
  });
});
