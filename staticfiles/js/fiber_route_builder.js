let map;
let polyline;
let currentPath = [];
let markers = [];
let activeFiberId = null;

const distanceEl = document.getElementById('distanceKm');

// Manual save modal elements
const manualModal = document.getElementById('manualSaveModal');
const manualModalContent = document.getElementById('manualSaveModalContent');
const manualForm = document.getElementById('manualSaveForm');
const manualRouteDistanceEl = document.getElementById('manualRouteDistance');
const manualRouteNameInput = document.getElementById('manualRouteName');
const manualOriginDeviceSelect = document.getElementById('manualOriginDeviceSelect');
const manualOriginPortSelect = document.getElementById('manualOriginPortSelect');
const manualSinglePortCheckbox = document.getElementById('manualSinglePortOnly');
const manualDestDeviceSelect = document.getElementById('manualDestDeviceSelect');
const manualDestPortSelect = document.getElementById('manualDestPortSelect');
const manualDestNotice = document.getElementById('manualDestNotice');

function haversineKm(pointA, pointB) {
    const earthRadiusKm = 6371;
    const dLat = (pointB.lat - pointA.lat) * Math.PI / 180;
    const dLng = (pointB.lng - pointA.lng) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 +
        Math.cos(pointA.lat * Math.PI / 180) *
        Math.cos(pointB.lat * Math.PI / 180) *
        Math.sin(dLng / 2) ** 2;
    return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function totalDistance() {
    let total = 0;
    for (let i = 0; i < currentPath.length - 1; i += 1) {
        total += haversineKm(currentPath[i], currentPath[i + 1]);
    }
    distanceEl.textContent = total.toFixed(3);
    return total;
}

function redrawPolyline() {
    if (polyline) {
        polyline.setMap(null);
    }
    polyline = new google.maps.Polyline({
        path: currentPath,
        map,
        strokeColor: '#2563eb',
        strokeWeight: 4,
        strokeOpacity: 0.9,
    });
}

function refreshList() {
    const list = document.getElementById('pointsList');
    list.innerHTML = '';
    currentPath.forEach((point, index) => {
        const item = document.createElement('li');
        item.className = 'point-row flex justify-between items-center';
        item.draggable = true;
        item.dataset.idx = index;
        item.innerHTML = `<span>${index + 1}. ${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}</span>`;

        item.addEventListener('dragstart', (event) => {
            event.dataTransfer.setData('text/plain', index);
            item.classList.add('bg-blue-100');
        });
        item.addEventListener('dragend', () => {
            item.classList.remove('bg-blue-100');
        });
        item.addEventListener('dragover', (event) => {
            event.preventDefault();
            item.classList.add('bg-blue-50');
        });
        item.addEventListener('dragleave', () => {
            item.classList.remove('bg-blue-50');
        });
        item.addEventListener('drop', (event) => {
            event.preventDefault();
            item.classList.remove('bg-blue-50');
            const fromIndex = parseInt(event.dataTransfer.getData('text/plain'), 10);
            const toIndex = parseInt(item.dataset.idx, 10);
            if (Number.isInteger(fromIndex) && Number.isInteger(toIndex) && fromIndex !== toIndex) {
                const moved = currentPath.splice(fromIndex, 1)[0];
                currentPath.splice(toIndex, 0, moved);
                setPath(currentPath);
            }
        });

        list.appendChild(item);
    });
    totalDistance();

    const saveButton = document.getElementById('savePath');
    if (saveButton) {
        const allowSave =
            (currentPath.length >= 2) ||
            (activeFiberId && currentPath.length === 0);
        saveButton.disabled = !allowSave;
    }
}

function clearMarkers() {
    markers.forEach((marker) => marker.setMap(null));
    markers = [];
}

function addMarker(point, removable = true) {
    const marker = new google.maps.Marker({ position: point, map, draggable: true });

    marker.addListener('dragend', () => {
        const index = markers.indexOf(marker);
        if (index > -1) {
            currentPath[index] = {
                lat: marker.getPosition().lat(),
                lng: marker.getPosition().lng(),
            };
            redrawPolyline();
            refreshList();
        }
    });

    if (removable) {
        const removeMarker = () => {
            const index = markers.indexOf(marker);
            if (index > -1) {
                markers.splice(index, 1);
                currentPath.splice(index, 1);
                marker.setMap(null);
                redrawPolyline();
                refreshList();
            }
        };

        marker.addListener('dblclick', removeMarker);
        marker.addListener('rightclick', removeMarker);
    }

    markers.push(marker);
}

function setPath(points) {
    clearMarkers();
    currentPath = points.slice();
    currentPath.forEach((point) => addMarker(point));
    redrawPolyline();
    refreshList();
}

function initMap() {
    map = new google.maps.Map(document.getElementById('builderMap'), {
        center: { lat: -16.6869, lng: -49.2648 },
        zoom: 6,
        mapTypeId: 'terrain',
    });

    map.addListener('click', (event) => {
        const point = { lat: event.latLng.lat(), lng: event.latLng.lng() };
        currentPath.push(point);
        addMarker(point);
        redrawPolyline();
        refreshList();
    });

    loadFibers();
}

window.initMap = initMap;

async function loadFibers() {
    const response = await fetch('/zabbix_api/api/fibers/');
    const data = await response.json();
    const select = document.getElementById('fiberSelect');
    select.innerHTML = '<option value="">-- select a cable --</option>';
    data.cables.forEach((cable) => {
        const option = document.createElement('option');
        option.value = cable.id;
        option.textContent = cable.name;
        select.appendChild(option);
    });
}

async function loadFiberDetail(id) {
    const response = await fetch(`/zabbix_api/api/fiber/${id}/`);
    if (!response.ok) {
        alert('Error loading cable');
        return;
    }
    const data = await response.json();
    activeFiberId = data.id;
    const path = (data.path && data.path.length)
        ? data.path
        : buildDefaultFromEndpoints(data);
    setPath(path);
}

function buildDefaultFromEndpoints(fiber) {
    const points = [];
    if (fiber.origin.lat != null && fiber.origin.lng != null) {
        points.push({ lat: fiber.origin.lat, lng: fiber.origin.lng });
    }
    if (fiber.destination.lat != null && fiber.destination.lng != null) {
        points.push({ lat: fiber.destination.lat, lng: fiber.destination.lng });
    }
    return points;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

async function updateExistingPath() {
    if (!activeFiberId) return;

    const csrftoken = getCookie('csrftoken');

    try {
        const response = await fetch(`/zabbix_api/api/fiber/${activeFiberId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({ path: currentPath }),
        });

        if (!response.ok) {
            const details = await response.text();
            alert(`Failed to save: ${details}`);
            return;
        }

        const payload = await response.json();
        alert(`Saved successfully.\nPoints: ${payload.points}\nDistance: ${payload.length_km} km`);
    } catch (error) {
        console.error('Request error:', error);
        alert('Connection failure or unexpected error while saving.');
    }
}

function resetManualSaveForm() {
    if (!manualForm) return;
    manualForm.reset();
    if (manualOriginPortSelect) {
        manualOriginPortSelect.innerHTML = '<option value="">Selecione...</option>';
    }
    if (manualDestPortSelect) {
        manualDestPortSelect.innerHTML = '<option value="">Selecione...</option>';
        manualDestPortSelect.disabled = false;
    }
    if (manualDestDeviceSelect) {
        manualDestDeviceSelect.disabled = false;
    }
    if (manualSinglePortCheckbox) {
        manualSinglePortCheckbox.checked = false;
    }
    if (manualDestNotice) {
        manualDestNotice.classList.add('hidden');
    }
}

function openManualSaveModal() {
    if (!manualModal || !manualModalContent) {
        console.warn('Manual save modal not found in the DOM.');
        return;
    }
    resetManualSaveForm();
    if (manualRouteDistanceEl) {
        const distance = totalDistance();
        manualRouteDistanceEl.textContent = `${distance.toFixed(3)} km`;
    }
    manualModal.classList.remove('pointer-events-none');
    manualModal.classList.add('opacity-100');
    manualModalContent.classList.add('opacity-100', 'scale-100');
    manualModalContent.classList.remove('opacity-0', 'scale-95');
    if (manualRouteNameInput) {
        requestAnimationFrame(() => manualRouteNameInput.focus());
    }
    syncDestinationDevice();
}

function closeManualSaveModal() {
    if (!manualModal || !manualModalContent) return;
    manualModal.classList.remove('opacity-100');
    manualModal.classList.add('opacity-0');
    manualModalContent.classList.remove('opacity-100', 'scale-100');
    manualModalContent.classList.add('opacity-0', 'scale-95');
    setTimeout(() => {
        manualModal.classList.add('pointer-events-none');
    }, 300);
}

async function loadPortsForSelect(deviceId, targetSelect) {
    if (!targetSelect) return;
    targetSelect.innerHTML = '<option value="">Carregando...</option>';
    if (!deviceId) {
        targetSelect.innerHTML = '<option value="">Selecione...</option>';
        return;
    }
    try {
        const response = await fetch(`/zabbix_api/api/device-ports/${deviceId}/`);
        if (!response.ok) {
            targetSelect.innerHTML = '<option value="">Falha ao carregar</option>';
            return;
        }
        const data = await response.json();
        targetSelect.innerHTML = '<option value="">Selecione...</option>';
        if (Array.isArray(data.ports)) {
            data.ports.forEach((port) => {
                const option = document.createElement('option');
                option.value = port.id;
                option.textContent = port.name;
                targetSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load ports:', error);
        targetSelect.innerHTML = '<option value="">Falha ao carregar</option>';
    }
}

async function syncDestinationDevice() {
    const singlePort = manualSinglePortCheckbox && manualSinglePortCheckbox.checked;

    if (manualDestNotice) {
        manualDestNotice.classList.toggle('hidden', !singlePort);
    }

    if (manualDestDeviceSelect) {
        manualDestDeviceSelect.disabled = singlePort;
        if (singlePort) {
            manualDestDeviceSelect.value = manualOriginDeviceSelect ? manualOriginDeviceSelect.value : '';
        }
    }

    if (manualDestPortSelect) {
        if (singlePort) {
            manualDestPortSelect.innerHTML = '<option value="">-- destino desabilitado --</option>';
            manualDestPortSelect.disabled = true;
        } else {
            manualDestPortSelect.disabled = false;
            if (manualDestDeviceSelect && manualDestDeviceSelect.value) {
                await loadPortsForSelect(manualDestDeviceSelect.value, manualDestPortSelect);
            } else {
                manualDestPortSelect.innerHTML = '<option value="">Selecione...</option>';
            }
        }
    }
}

async function createManualFiber(event) {
    event.preventDefault();
    if (currentPath.length < 2) {
        alert('Adicione pelo menos dois pontos ao mapa antes de salvar a rota.');
        return;
    }

    const formData = new FormData(manualForm);
    const singlePort = manualSinglePortCheckbox && manualSinglePortCheckbox.checked;

    const payload = {
        name: (formData.get('name') || '').trim(),
        origin_device_id: formData.get('origin_device_id'),
        origin_port_id: formData.get('origin_port_id'),
        dest_device_id: singlePort
            ? formData.get('origin_device_id')
            : formData.get('dest_device_id'),
        dest_port_id: singlePort ? null : formData.get('dest_port_id'),
        single_port: singlePort,
        path: currentPath.map((point) => ({ lat: point.lat, lng: point.lng })),
    };

    if (!payload.name || !payload.origin_device_id || !payload.origin_port_id) {
        alert('Preencha todos os campos obrigatórios.');
        return;
    }
    if (!singlePort && !payload.dest_port_id) {
        alert('Preencha todos os campos obrigatórios.');
        return;
    }

    const submitButton = manualForm.querySelector('button[type="submit"]');
    if (submitButton) submitButton.disabled = true;

    try {
        const csrftoken = getCookie('csrftoken');
        const response = await fetch('/zabbix_api/api/fibers/manual-create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
            alert(`Falha ao salvar rota: ${data.error || 'Erro inesperado'}`);
            return;
        }

        activeFiberId = data.fiber_id;
        await loadFibers();
        const fiberSelect = document.getElementById('fiberSelect');
        if (fiberSelect) {
            fiberSelect.value = String(data.fiber_id);
        }
        refreshList();
        alert('Rota criada com sucesso.');
        closeManualSaveModal();
    } catch (error) {
        console.error('Erro ao criar rota manual:', error);
        alert('Falha de conexão ou erro inesperado ao criar a rota.');
    } finally {
        if (submitButton) submitButton.disabled = false;
    }
}

function handleSaveClick() {
    if (activeFiberId) {
        updateExistingPath();
        return;
    }
    if (currentPath.length < 2) {
        alert('Adicione pelo menos dois pontos ao mapa antes de salvar a rota.');
        return;
    }
    openManualSaveModal();
}

async function deleteCable() {
    if (!activeFiberId) {
        alert('No cable selected to delete.');
        return;
    }

    if (!confirm('Confirm cable deletion? This action cannot be undone.')) {
        return;
    }

    const csrftoken = getCookie('csrftoken');

    try {
        const response = await fetch(`/zabbix_api/api/fiber/${activeFiberId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrftoken,
            },
        });

        if (response.status === 204) {
            alert('Cable removed successfully.');
            activeFiberId = null;
            setPath([]);
            loadFibers();
        } else {
            const details = await response.text();
            alert(`Failed to delete: ${details}`);
        }
    } catch (error) {
        console.error('Request error:', error);
        alert('Connection failure or unexpected error while deleting.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('loadFiber').addEventListener('click', () => {
        const id = document.getElementById('fiberSelect').value;
        if (!id) {
            alert('Select a cable first.');
            return;
        }
        loadFiberDetail(id);
    });
    document.getElementById('clearPath').addEventListener('click', () => {
        setPath([]);
    });
    document.getElementById('savePath').addEventListener('click', handleSaveClick);
    document.getElementById('deleteCable').addEventListener('click', deleteCable);

    if (manualForm) {
        manualForm.addEventListener('submit', createManualFiber);
    }
    if (manualOriginDeviceSelect) {
        manualOriginDeviceSelect.addEventListener('change', async () => {
            await loadPortsForSelect(manualOriginDeviceSelect.value, manualOriginPortSelect);
            await syncDestinationDevice();
        });
    }
    if (manualDestDeviceSelect) {
        manualDestDeviceSelect.addEventListener('change', async () => {
            if (manualDestDeviceSelect.disabled) return;
            await loadPortsForSelect(manualDestDeviceSelect.value, manualDestPortSelect);
        });
    }
    if (manualSinglePortCheckbox) {
        manualSinglePortCheckbox.addEventListener('change', () => {
            syncDestinationDevice();
        });
    }
    if (manualModal) {
        manualModal.addEventListener('click', (event) => {
            if (event.target === manualModal) {
                closeManualSaveModal();
            }
        });
    }

    syncDestinationDevice();
});

window.closeManualSaveModal = closeManualSaveModal;
