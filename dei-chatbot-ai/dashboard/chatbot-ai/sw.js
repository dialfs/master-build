/* ============================================================
 * DEI Chatbot Dashboard - Service Worker
 * v1.2.8 - Web Push + PWA
 * ============================================================ */

// --- Push event: tampilkan notifikasi (jalan meski dashboard/browser ketutup) ---
self.addEventListener('push', function (event) {
  var data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: 'DEI', body: (event.data ? event.data.text() : '') };
  }

  var title = data.title || 'DEI Chatbot';
  var options = {
    body: data.body || 'Pesan baru masuk',
    icon: data.icon || './icon-192.png',
    badge: './icon-192.png',
    tag: data.tag || 'dei-notif',          // group notif per-chat (tag sama = replace)
    renotify: true,                         // getar/bunyi lagi meski tag sama
    requireInteraction: false,              // auto-dismiss (true = harus di-klik)
    data: {
      url: data.url || './',                // URL dibuka saat notif di-klik
      ts: Date.now()
    }
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// --- Notification click: buka/fokus ke dashboard di URL terkait ---
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var targetUrl = (event.notification.data && event.notification.data.url) || './';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      // Kalau dashboard sudah kebuka, fokuskan + navigate
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if ('focus' in client) {
          client.focus();
          if ('navigate' in client && targetUrl !== './') {
            try { client.navigate(targetUrl); } catch (e) {}
          }
          return;
        }
      }
      // Kalau belum ada window, buka baru
      if (clients.openWindow) return clients.openWindow(targetUrl);
    })
  );
});

// --- Install: aktif langsung (skip waiting) ---
self.addEventListener('install', function (event) {
  self.skipWaiting();
});

// --- Activate: claim semua client langsung ---
self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});
