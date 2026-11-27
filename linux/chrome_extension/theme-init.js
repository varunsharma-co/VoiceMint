(function() {
  const theme = localStorage.getItem("voice_mint_theme");
  if (theme === "dark") {
    document.body.classList.add("dark-mode");
  }
})();