// Script resiliente para modal de importação KML
const kmlModal = document.getElementById('importKmlModal');
const kmlModalContent = document.getElementById('importKmlModalContent');

function openKmlModal() {
    if (!kmlModal || !kmlModalContent) return console.warn('Modal KML não encontrado no DOM');
    kmlModal.classList.remove('pointer-events-none');
    kmlModal.classList.add('opacity-100');
    kmlModalContent.classList.add('opacity-100', 'scale-100');
    kmlModalContent.classList.remove('opacity-0', 'scale-95');
}

function closeKmlModal() {
    if (!kmlModal || !kmlModalContent) return;
    kmlModal.classList.remove('opacity-100');
    kmlModal.classList.add('opacity-0');
    kmlModalContent.classList.remove('opacity-100', 'scale-100');
    kmlModalContent.classList.add('opacity-0', 'scale-95');
    setTimeout(() => {
        if (kmlModal) kmlModal.classList.add('pointer-events-none');
    }, 300);
}

function attachSelectLoader(selectId, portSelectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    el.addEventListener('change', async function () {
        const deviceId = this.value;
        const portSelect = document.getElementById(portSelectId);
        if (!portSelect) return;
        portSelect.innerHTML = '<option value="">Selecione...</option>';
        if (!deviceId) return;
        try {
            const resp = await fetch(`/zabbix_api/api/device-ports/${deviceId}/`);
            const data = await resp.json();
            if (resp.ok && data.ports) {
                data.ports.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.name;
                    portSelect.appendChild(opt);
                });
            }
        } catch (err) {
            portSelect.innerHTML = '<option value="">Erro ao carregar</option>';
        }
    });
}

attachSelectLoader('originDeviceSelect', 'originPortSelect');
attachSelectLoader('destDeviceSelect', 'destPortSelect');

const importFormEl = document.getElementById('importKmlForm');
if (importFormEl) {
    importFormEl.addEventListener('submit', async function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        try {
            const resp = await fetch('/zabbix_api/api/fibers/import-kml/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData,
            });
            const data = await resp.json();
            if (resp.ok) {
                alert('Importação concluída com sucesso! Pontos importados: ' + (data.points || '?'));
                closeKmlModal();
            } else {
                alert('Erro ao importar: ' + (data.error || 'Falha no upload'));
            }
        } catch (err) {
            console.error(err);
            alert('Erro de rede ou servidor durante o upload.');
        }
    });
}

if (kmlModal) {
    kmlModal.addEventListener('click', (e) => {
        if (e.target === kmlModal) closeKmlModal();
    });
}