document.addEventListener('DOMContentLoaded', function() {
  
  // ========================================= 
  // DROPDOWN DO USUÁRIO
  // ========================================= 
  const userMenuButton = document.getElementById('userMenuButton');
  const userMenuDropdown = document.getElementById('userMenuDropdown');
  const userMenuArrow = document.getElementById('userMenuArrow');

  if (userMenuButton && userMenuDropdown) {
    // Toggle dropdown do usuário
    userMenuButton.addEventListener('click', function(e) {
      e.stopPropagation();
      const isHidden = userMenuDropdown.classList.contains('hidden');
      
      if (isHidden) {
        userMenuDropdown.classList.remove('hidden');
        userMenuArrow.style.transform = 'rotate(180deg)';
      } else {
        userMenuDropdown.classList.add('hidden');
        userMenuArrow.style.transform = 'rotate(0deg)';
      }
    });

    // Fechar dropdown ao clicar fora
    document.addEventListener('click', function(e) {
      if (!userMenuButton.contains(e.target) && !userMenuDropdown.contains(e.target)) {
        userMenuDropdown.classList.add('hidden');
        userMenuArrow.style.transform = 'rotate(0deg)';
      }
    });

    // Fechar dropdown com ESC
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        userMenuDropdown.classList.add('hidden');
        userMenuArrow.style.transform = 'rotate(0deg)';
      }
    });
  }

  // ========================================= 
  // ALTERNADOR DE TEMA (se existir)
  // ========================================= 
  const themeToggle = document.getElementById('themeToggle');
  const iconSun = document.getElementById('iconSun');
  const iconMoon = document.getElementById('iconMoon');

  if (themeToggle && iconSun && iconMoon) {
    // Verificar tema atual
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.classList.toggle('dark', currentTheme === 'dark');
    
    // Mostrar ícone correto
    if (currentTheme === 'dark') {
      iconSun.classList.remove('hidden');
      iconMoon.classList.add('hidden');
    } else {
      iconSun.classList.add('hidden');
      iconMoon.classList.remove('hidden');
    }

    // Toggle de tema
    themeToggle.addEventListener('click', function() {
      const isDark = document.documentElement.classList.contains('dark');
      
      if (isDark) {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        iconSun.classList.add('hidden');
        iconMoon.classList.remove('hidden');
      } else {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        iconSun.classList.remove('hidden');
        iconMoon.classList.add('hidden');
      }
    });
  }

  // ========================================= 
  // MENU MOBILE (se existir)
  // ========================================= 
  const mobileToggle = document.querySelector('[data-mobile-toggle]');
  const mobileNav = document.getElementById('mobileNav');

  if (mobileToggle && mobileNav) {
    mobileToggle.addEventListener('click', function() {
      const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
      
      mobileToggle.setAttribute('aria-expanded', !isExpanded);
      mobileNav.classList.toggle('hidden');
    });
  }
});