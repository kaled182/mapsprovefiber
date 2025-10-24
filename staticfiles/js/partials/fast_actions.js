document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('manualActionsButton');
    const dropdown = document.getElementById('manualActionsDropdown');
    const arrow = document.getElementById('fastactionsMenuArrow'); // seta opcional (SVG dentro do botão)

    if (!button || !dropdown) return; // segurança

    // Alterna visibilidade ao clicar no botão
    button.addEventListener('click', (e) => {
        e.stopPropagation();
        const isHidden = dropdown.classList.contains('hidden');

        // Alterna visibilidade
        dropdown.classList.toggle('hidden', !isHidden);

        // Rotaciona a seta (se existir)
        if (arrow) arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
    });

    // Fecha dropdown ao clicar fora
    document.addEventListener('click', (e) => {
        if (!dropdown.classList.contains('hidden') && !e.target.closest('#manualActionsMenu')) {
            dropdown.classList.add('hidden');
            if (arrow) arrow.style.transform = 'rotate(0deg)';
        }
    });

    // Fecha dropdown com tecla ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !dropdown.classList.contains('hidden')) {
            dropdown.classList.add('hidden');
            if (arrow) arrow.style.transform = 'rotate(0deg)';
        }
    });
});
