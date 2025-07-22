// Prykladowy frontend w js, dotyczy implementaji w pliku app_handler.py
//1. Pobieranie wszystkich parametrów urządzenia:

async function getDeviceParameters(deviceId) {
  const response = await fetch(`/app/devices/${deviceId}/parameters`);
  return await response.json();
}

//2. Pobieranie konkretnego parametru:
async function getParameter(deviceId, paramAddress) {
  const response = await fetch(`/app/devices/${deviceId}/parameters/${paramAddress}`);
  return await response.json();
}

// 3. Aktualizacja parametru:
async function updateParameter(deviceId, paramAddress, paramData) {
  const response = await fetch(`/app/devices/${deviceId}/parameters/${paramAddress}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ param_data: paramData })
});
  return await response.json();
}
// 4. Aktualizacja parametru (alternatywny endpoint):

async function updateServiceParameter(deviceId, paramAddress, paramData) {
  const response = await fetch('/app/service-parameter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      device_id: deviceId,
      param_address: paramAddress,
      param_data: paramData
    })
  });
  return await response.json();
}
