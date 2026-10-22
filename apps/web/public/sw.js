// ASTRA-GUARD Service Worker for Web Push & PWA Notifications
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: "ASTRA-GUARD Alert", body: event.data.text() };
    }
  }

  const title = data.title || "[ASTRA-GUARD] Operational Alert";
  const options = {
    body: data.body || "High-priority mission safety advisory recorded.",
    icon: data.icon || "/icons/icon-192x192.png",
    badge: data.badge || "/icons/badge-72x72.png",
    tag: data.tag || "astraguard-alert",
    data: data.data || {},
    actions: data.actions || [],
    vibrate: [200, 100, 200, 100, 200],
    requireInteraction: true,
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const notifData = event.notification.data || {};
  const action = event.action;

  // Handle inline notification action button click (e.g., 'approve', 'snooze')
  if (action && notifData.actions) {
    const actionObj = notifData.actions.find((a) => a.action === action);
    if (actionObj && actionObj.url) {
      event.waitUntil(
        fetch(actionObj.url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        })
          .then((resp) => {
            if (resp.ok) {
              return self.registration.showNotification(
                `ASTRA-GUARD: Action Executed`,
                {
                  body: `Signed operator action '${action.toUpperCase()}' recorded in mission audit trail.`,
                  tag: event.notification.tag,
                  icon: "/icons/icon-192x192.png",
                }
              );
            }
          })
          .catch((err) => {
            console.error("Failed to execute signed action from push:", err);
          })
      );
      return;
    }
  }

  // Fallback: Click on notification body opens or focuses web console
  const targetUrl = notifData.url || "/dashboard/alerts";
  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windowClients) => {
        for (const client of windowClients) {
          if (client.url.includes(targetUrl) && "focus" in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});
