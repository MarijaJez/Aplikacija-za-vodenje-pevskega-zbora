const pushButton = document.querySelector('[data-push-toggle]');
const pushStatus = document.querySelector('[data-push-status]');
const pushTestButton = document.querySelector('[data-push-test]');

if (pushButton && pushStatus) {
  let publicKey = '';
  let subscribed = false;

  function setStatus(message, available = true) {
    pushStatus.textContent = message;
    pushButton.disabled = !available;
    pushButton.textContent = subscribed ? 'Izklopi obvestila' : 'Vklopi obvestila';
    if (pushTestButton) pushTestButton.hidden = !subscribed;
  }

  function decodeBase64Url(value) {
    const binary = atob(value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4));
    return Uint8Array.from(binary, character => character.charCodeAt(0));
  }

  async function registration() {
    return navigator.serviceWorker.register('/sw.js');
  }

  async function refresh() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window) || !window.isSecureContext) {
      setStatus('Ta brskalnik ne podpira potisnih obvestil.', false);
      return;
    }
    try {
      const configResponse = await fetch('/api/push/config', { credentials: 'same-origin' });
      if (!configResponse.ok) throw new Error('config');
      const config = await configResponse.json();
      if (!config.enabled) {
        setStatus('Potisna obvestila na strežniku še niso nastavljena.', false);
        return;
      }
      publicKey = config.publicKey;
      const subscription = await (await registration()).pushManager.getSubscription();
      if (subscription) {
        const statusResponse = await fetch(`/api/push/status?endpoint=${encodeURIComponent(subscription.endpoint)}`, { credentials: 'same-origin' });
        subscribed = statusResponse.ok && (await statusResponse.json()).subscribed;
      }
      setStatus(subscribed ? 'Obvestila o dogodkih in klepetu so vključena.' : 'Prejemaj obvestila o dogodkih in novih sporočilih v klepetu.');
    } catch {
      setStatus('Stanja obvestil trenutno ni mogoče preveriti.', false);
    }
  }

  pushButton.addEventListener('click', async () => {
    pushButton.disabled = true;
    try {
      // Ask only after this explicit user click; browsers require user activation.
      const permission = subscribed ? Notification.permission : await Notification.requestPermission();
      if (permission !== 'granted') {
        setStatus('Dovoli obvestila v nastavitvah brskalnika.', false);
        return;
      }
      const manager = (await registration()).pushManager;
      let subscription = await manager.getSubscription();
      if (subscribed) {
        if (subscription) {
          const result = await fetch('/api/push/unsubscribe', {
            method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ endpoint: subscription.endpoint })
          });
          if (!result.ok) throw new Error('unsubscribe');
          try { await subscription.unsubscribe(); } catch { /* Server opt-out already succeeded. */ }
        }
        subscribed = false;
        setStatus('Obvestila so izključena.');
      } else {
        subscription ||= await manager.subscribe({ userVisibleOnly: true, applicationServerKey: decodeBase64Url(publicKey) });
        const result = await fetch('/api/push/subscriptions', {
          method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(subscription.toJSON())
        });
        if (!result.ok) throw new Error('subscribe');
        subscribed = true;
        setStatus('Obvestila o dogodkih in klepetu so vključena.');
      }
    } catch {
      setStatus('Nastavitve obvestil ni bilo mogoče shraniti. Poskusi znova.');
    }
  });
  pushTestButton?.addEventListener('click', async () => {
    pushTestButton.disabled = true;
    try {
      const result = await fetch('/api/push/test', {
        method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}'
      });
      if (!result.ok) throw new Error('test');
      pushStatus.textContent = 'Preizkusno obvestilo je poslano.';
    } catch {
      pushStatus.textContent = 'Preizkusnega obvestila ni bilo mogoče poslati.';
    } finally {
      pushTestButton.disabled = false;
    }
  });
  refresh();
}
