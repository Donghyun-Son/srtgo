self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());

let controller = null;

self.addEventListener('message', event => {
  if (event.data.type === 'reserve') {
    controller = new AbortController();
    reserve(event.data.payload, event.source);
  } else if (event.data.type === 'cancel' && controller) {
    controller.abort();
  }
});

async function reserve(payload, source) {
  try {
    const resp = await fetch('/reserve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-Token': payload.token
      },
      body: JSON.stringify(payload.data),
      signal: controller.signal
    });
    const data = await resp.json();
    self.registration.showNotification('Reservation complete');
    if (source) source.postMessage({type:'reserve-result', success:true, data});
  } catch (err) {
    if (err.name === 'AbortError') return;
    self.registration.showNotification('Reservation failed');
    if (source) source.postMessage({type:'reserve-result', success:false, error:err.toString()});
  }
}
