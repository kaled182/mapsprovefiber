const modal = document.getElementById('addDeviceModal');
const modalContent = document.getElementById('addDeviceModalContent');

function openModal() {
    modal.classList.remove('pointer-events-none');
    modal.classList.add('opacity-100');
    modalContent.classList.add('opacity-100', 'scale-100');
    modalContent.classList.remove('opacity-0', 'scale-95');
}

function closeModal() {
    modal.classList.remove('opacity-100');
    modal.classList.add('opacity-0');
    modalContent.classList.remove('opacity-100', 'scale-100');
    modalContent.classList.add('opacity-0', 'scale-95');
    setTimeout(() => {
        modal.classList.add('pointer-events-none');
    }, 300); // igual à duração da animação
}

// Submissão (exemplo)
document.getElementById('addDeviceForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const hostid = formData.get('device_name');
    try {
        const resp = await fetch('/zabbix_api/api/add-device-from-zabbix/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ hostid })
        });
        const data = await resp.json();
        if (resp.ok) {
            alert('Device adicionado: ' + data.device.name + ' (site: ' + data.device.site + ')');
            closeModal();
        } else {
            alert('Erro: ' + (data.error || 'Falha ao adicionar device'));
        }
    } catch (err) {
        alert('Erro de rede ou servidor');
    }
});

// Fechar ao clicar fora
modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});