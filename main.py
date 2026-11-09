import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

app = FastAPI()

MANIFEST_JSON = """{
  "short_name": "TikTok Live",
  "name": "TikTok Live Ultimate Dashboard",
  "icons": [
    {
      "src": "/icon.png",
      "type": "image/svg+xml",
      "sizes": "192x192 512x512",
      "purpose": "any maskable"
    }
  ],
  "start_url": "/",
  "background_color": "#0f0f0f",
  "theme_color": "#0f0f0f",
  "display": "standalone",
  "orientation": "portrait"
}"""

SERVICE_WORKER_JS = """
self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => { e.waitUntil(clients.claim()); });
self.addEventListener('fetch', (event) => { event.respondWith(fetch(event.request)); });
"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" rx="100" fill="#0f0f0f"/>
  <circle cx="256" cy="256" r="180" fill="#18181b" stroke="#25F4EE" stroke-width="12"/>
  <path d="M180 160 L360 256 L180 352 Z" fill="#FE2C55"/>
  <text x="256" y="420" text-anchor="middle" fill="#25F4EE" font-family="sans-serif" font-weight="bold" font-size="48">LIVE</text>
</svg>"""

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <!-- PWA Meta Tags per installazione nativa -->
    <link rel="manifest" href="/manifest.json">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#0f0f0f">
    <link rel="icon" type="image/svg+xml" href="/icon.png">
    <link rel="apple-touch-icon" href="/icon.png">

    <title>TikTok Live Ultimate Dashboard - Stalker Edition</title>
    <script src="https://cdn.jsdelivr.net/npm/mpegts.js@1.7.3/dist/mpegts.js"></script>
    <style>
        body { background: #0f0f0f; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0; overflow: hidden; }
        header { background: #18181b; padding: 12px 20px; border-bottom: 1px solid #27272a; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px; z-index: 10; }
        .brand { font-weight: bold; font-size: 16px; color: #25F4EE; display: flex; align-items: center; gap: 8px; }
        .controls-bar { display: flex; gap: 10px; flex: 1; max-width: 500px; min-width: 200px; }
        input { flex: 1; padding: 10px 14px; border-radius: 6px; border: 1px solid #3f3f46; background: #27272a; color: #fff; font-size: 14px; outline: none; }
        input:focus { border-color: #25F4EE; }
        button { padding: 10px 20px; background: #FE2C55; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; white-space: nowrap; }
        button:hover { opacity: 0.9; }
        
        /* Stats Header Widget */
        .stats-widget { display: flex; gap: 15px; font-size: 13px; font-weight: bold; color: #a1a1aa; align-items: center; }
        .stat-item { background: #27272a; padding: 6px 12px; border-radius: 4px; border: 1px solid #3f3f46; display: flex; gap: 6px; align-items: center; }
        .stat-item span { color: #25F4EE; }
        .stat-item.likes span { color: #FE2C55; }

        .main-container { display: flex; flex: 1; overflow: hidden; position: relative; background: #000; }
        .main-container.twitch-mode { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; }
        
        .player-section { flex: 1; display: flex; flex-direction: column; background: #000; position: relative; height: 100%; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: contain; background: #000; outline: none; }
        
        #status-overlay { 
            position: absolute; bottom: 65px; left: 20px; right: 20px;
            background: rgba(0,0,0,0.85); padding: 10px 14px; border-radius: 6px; 
            font-size: 13px; color: #e4e4e7; border: 1px solid rgba(255,255,255,0.1); 
            pointer-events: none; z-index: 5; 
            transition: opacity 0.5s ease; opacity: 1; 
        }
        #status-overlay.fade-out { opacity: 0; }

        .chat-section { width: 340px; min-width: 300px; background: #121212; border-left: 1px solid #27272a; display: flex; flex-direction: column; transition: all 0.2s ease; z-index: 10; }
        .twitch-mode .chat-section { width: 320px; background: rgba(18, 18, 18, 0.88); backdrop-filter: blur(8px); border-left: 1px solid rgba(255,255,255,0.1); }
        
        .chat-header { padding: 12px 15px; font-weight: bold; border-bottom: 1px solid #27272a; font-size: 13px; background: #18181b; color: #a1a1aa; display: flex; justify-content: space-between; align-items: center; }
        .twitch-mode .chat-header { background: rgba(24, 24, 27, 0.9); }
        
        .toggle-btn { background: #27272a; border: 1px solid #3f3f46; color: #fff; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .toggle-btn:hover { background: #3f3f46; }

        #chat { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
        
        .msg { background: rgba(24, 24, 27, 0.8); padding: 8px 12px; border-radius: 6px; font-size: 13px; border-left: 3px solid #25F4EE; line-height: 1.4; word-break: break-word; }
        .msg span { font-weight: bold; color: #25F4EE; display: inline-block; margin-right: 6px; }
        
        .msg.gift { border-left-color: #FE2C55; background: rgba(254, 44, 85, 0.15); }
        .msg.gift span { color: #FE2C55; }

        .msg.like { border-left-color: #FFD700; background: rgba(255, 215, 0, 0.1); }
        .msg.like span { color: #FFD700; }

        /* Responsive Mobile Layout */
        @media (max-width: 768px) {
            .main-container { flex-direction: column; }
            .player-section { height: 40vh; flex: initial; }
            .chat-section { width: 100%; flex: 1; border-left: none; border-top: 1px solid #27272a; }
            #status-overlay { bottom: 15px; }
        }
    </style>
</head>
<body>

    <header id="mainHeader">
        <div class="brand">⚡ TIKTOK LIVE STALKER</div>
        <div class="controls-bar">
            <input type="text" id="username" placeholder="Username (es. f.m.spettacoli)" />
            <button onclick="startLive()">Avvia Stream</button>
        </div>
        <div class="stats-widget">
            <div class="stat-item">👁️ Spettatori: <span id="viewerCount">0</span></div>
            <div class="stat-item likes">❤️ Likes: <span id="likeCount">0</span></div>
        </div>
    </header>

    <div class="main-container" id="mainContainer">
        <div class="player-section">
            <video id="videoPlayer" controls autoplay muted playsinline></video>
            <div id="status-overlay">Inserisci un username e premi Avvia Stream...</div>
        </div>
        
        <div class="chat-section" id="chatSection">
            <div class="chat-header">
                <span>💬 CHAT & GIFT REALTIME</span>
                <button class="toggle-btn" onclick="toggleTwitchMode()">📺 Modalità Twitch</button>
            </div>
            <div id="chat"></div>
        </div>
    </div>

    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js').catch(e => console.log('SW error:', e));
        }

        let player = null;
        let chatInterval = null;
        let currentRoomId = null;
        let currentCursor = "0";
        let currentGiftCursor = "0";
        let statusTimeout = null;
        let messageQueue = [];
        let isProcessingQueue = false;

        function showStatus(text, autoHide = false) {
            const overlay = document.getElementById('status-overlay');
            overlay.innerText = text;
            overlay.classList.remove('fade-out');
            
            if (statusTimeout) clearTimeout(statusTimeout);
            
            if (autoHide) {
                statusTimeout = setTimeout(() => {
                    overlay.classList.add('fade-out');
                }, 3500);
            }
        }

        async function startLive() {
            let username = document.getElementById('username').value.trim();
            if (!username) return alert("Inserisci un username!");
            username = username.replace('@', '');
            
            showStatus("Connessione a @" + username + " in corso...");
            
            if (chatInterval) clearInterval(chatInterval);
            currentCursor = "0";
            currentGiftCursor = "0";
            messageQueue = [];

            try {
                let res = await fetch(`/api/stream/${username}`);
                let data = await res.json();
                
                if (data.stream_url && data.room_id) {
                    currentRoomId = data.room_id;
                    showStatus("✅ Flusso attivo per @" + username, true);
                    playFlv(data.stream_url);
                    
                    const chatBox = document.getElementById('chat');
                    chatBox.innerHTML = '';
                    addChatMsgDirect("Sistema", "Connessione stabilita con successo.", "msg");

                    chatInterval = setInterval(fetchChatFeed, 1000);
                } else {
                    showStatus("⚠️ Impossibile trovare il flusso (utente offline).");
                }
            } catch(e) {
                showStatus("❌ Errore di comunicazione.");
            }
        }

        async function fetchChatFeed() {
            if (!currentRoomId) return;
            try {
                let res = await fetch(`/api/feed?room_id=${currentRoomId}&cursor=${currentCursor}&gift_cursor=${currentGiftCursor}`);
                let data = await res.json();
                
                if (data.cursor) currentCursor = data.cursor;
                if (data.giftCursor) currentGiftCursor = data.giftCursor;

                if (data.stats) {
                    document.getElementById('viewerCount').innerText = data.stats.user_count || 0;
                    document.getElementById('likeCount').innerText = data.stats.like_count || data.stats.digg_count || 0;
                }

                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(m => {
                        let formattedText = formatEmojis(m.text);
                        messageQueue.push({ user: m.nickname || m.username, text: formattedText, type: 'msg' });
                    });
                }

                if (data.gifts && data.gifts.length > 0) {
                    data.gifts.forEach(g => {
                        let giftText = `🎁 Ha inviato ${g.gift_name || 'un regalo'} (x${g.repeat_count || 1})!`;
                        messageQueue.push({ user: g.nickname || g.username, text: giftText, type: 'gift' });
                    });
                }

                if (data.likes && data.likes.length > 0) {
                    data.likes.forEach(l => {
                        let likeText = `❤️ Ha fatto ${l.count || 1} tap sullo schermo!`;
                        messageQueue.push({ user: l.nickname || l.username, text: likeText, type: 'like' });
                    });
                }

                processMessageQueue();
            } catch(e) {
                console.log("Errore fetch feed chat:", e);
            }
        }

        function processMessageQueue() {
            if (isProcessingQueue || messageQueue.length === 0) return;
            isProcessingQueue = true;

            const batchSize = Math.min(messageQueue.length, 5);
            for (let i = 0; i < batchSize; i++) {
                const msgData = messageQueue.shift();
                addChatMsgDirect(msgData.user, msgData.text, msgData.type);
            }

            setTimeout(() => {
                isProcessingQueue = false;
                if (messageQueue.length > 0) {
                    processMessageQueue();
                }
            }, 50);
        }

        function formatEmojis(text) {
            if (!text) return "";
            const emojiMap = {
                '[heart]': '❤️',
                '[love]': '😍',
                '[fire]': '🔥',
                '[laugh]': '😂',
                '[smile]': '😊',
                '[applause]': '👏',
                '[rose]': '🌹',
                '[thumbsup]': '👍',
                '[cool]': '😎'
            };
            return text.replace(/\[([a-zA-Z0-9]+)\]/g, (match, tag) => {
                return emojiMap[match.toLowerCase()] || match;
            });
        }

        function playFlv(url) {
            const videoElement = document.getElementById('videoPlayer');
            
            if (mpegts.getFeatureList().mseLivePlayback) {
                if (player) {
                    player.destroy();
                }
                player = mpegts.createPlayer({
                    type: 'flv',
                    isLive: true,
                    url: url
                }, {
                    enableWorker: false,
                    lazyLoadMaxDuration: 3 * 60,
                    seekType: 'range',
                });
                
                player.attachMediaElement(videoElement);
                player.load();
                player.play().catch(e => {
                    showStatus("⚠️ Autoplay bloccato, premi play sul player.");
                });
            } else {
                alert("Il browser non supporta mpegts.js MSE.");
            }
        }

        function addChatMsgDirect(user, text, type) {
            const chatBox = document.getElementById('chat');
            const div = document.createElement('div');
            
            if (type === 'gift') {
                div.className = "msg gift";
            } else if (type === 'like') {
                div.className = "msg like";
            } else {
                div.className = "msg";
            }
            
            div.innerHTML = `<span>${user}:</span> ${text}`;
            chatBox.appendChild(div);
            
            if (chatBox.children.length > 100) {
                chatBox.removeChild(chatBox.firstChild);
            }
            
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function toggleTwitchMode() {
            const container = document.getElementById('mainContainer');
            const btn = document.querySelector('.toggle-btn');
            
            container.classList.toggle('twitch-mode');
            
            if (container.classList.contains('twitch-mode')) {
                btn.innerText = "✕ Esci da Twitch Mode";
            } else {
                btn.innerText = "📺 Modalità Twitch";
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML_CONTENT)

@app.get("/manifest.json")
async def manifest():
    return Response(content=MANIFEST_JSON, media_type="application/json")

@app.get("/sw.js")
async def service_worker():
    return Response(content=SERVICE_WORKER_JS, media_type="application/javascript")

@app.get("/icon.png")
async def icon():
    return Response(content=ICON_SVG, media_type="image/svg+xml")

@app.get("/api/stream/{username}")
async def get_stream(username: str):
    api_url = "https://tiktokstalker.com/api/tiktok/get-live"
    payload = {"username": username}
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://tiktokstalker.com",
        "Referer": "https://tiktokstalker.com/it/tiktok-live-viewer",
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                res_data = response.json()
                data = res_data.get("data", {})
                room_id = data.get("roomId", "")
                streams = data.get("streams", [])
                
                stream_url = ""
                for s in streams:
                    flv = s.get("flv", "")
                    if s.get("codec") == "h264" and flv:
                        stream_url = flv
                        break
                
                if not stream_url:
                    for s in streams:
                        flv = s.get("flv", "")
                        if flv:
                            stream_url = flv
                            break
                            
                return {"stream_url": stream_url, "room_id": room_id}
    except Exception as e:
        print(f"Errore stream: {e}")
    return {"stream_url": "", "room_id": ""}

@app.get("/api/feed")
async def get_feed(room_id: str, cursor: str = "0", gift_cursor: str = "0"):
    feed_url = "https://tiktokstalker.com/api/tiktok/get-live-chat"
    payload = {
        "room_id": room_id,
        "cursor": cursor,
        "gift_cursor": gift_cursor
    }
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://tiktokxls.com" if False else "https://tiktokstalker.com",
        "Origin": "https://tiktokstalker.com",
        "Referer": "https://tiktokstalker.com/it/tiktok-live-viewer",
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(feed_url, json=payload, headers=headers)
            if response.status_code == 200:
                res_data = response.json()
                return res_data.get("data", {"messages": [], "gifts": [], "likes": [], "stats": {}, "cursor": cursor, "giftCursor": gift_cursor})
    except Exception as e:
        print(f"Errore feed chat stalker: {e}")
    return {"messages": [], "gifts": [], "likes": [], "stats": {}, "cursor": cursor, "giftCursor": gift_cursor}
