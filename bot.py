import asyncio

import requests

from fastapi import FastAPI, Request

from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from authlib.integrations.starlette_client import OAuth

from starlette.middleware.sessions import SessionMiddleware

from fastapi.responses import RedirectResponse

import os


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

GROQ_API_KEY = "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"

API_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL = "openai/gpt-oss-120b"

GOOGLE_CLIENT_ID = "68632825614-tfjkfpe616jrcfjl02l0k5gd8ar25jbj.apps.googleusercontent.com"

GOOGLE_CLIENT_SECRET = "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"

app = FastAPI()

oauth = OAuth()

oauth.register(

    name="google",

    client_id=GOOGLE_CLIENT_ID,

    client_secret=GOOGLE_CLIENT_SECRET,

    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",

    client_kwargs={"scope": "openid email profile"},

)

app.add_middleware(
    SessionMiddleware,
    secret_key="SUPER_SECRET_KEY_123",
    session_cookie="senya_session",
    same_site="lax",
    https_only=False
)

registered_users = {}

SYSTEM_PROMPT = """Ты — Сеня, мой личный ИИ-помощник. Никто другой, только Сеня. Отвечай на вопросы по текстам, кодам, домашке и проектам. Генерируй очень быстро, проффисеонально. Не здоровайся каждый раз, 1 раз в чате и все. Лимит сообщения: 3-5 абзацев, пиши подробно, если просят. Если спрашивают, кто ты — говори, что ты Сеня, ИИ, созданный на основе разных технологий. Никогда не называй свою модель. Не используй LaTeX, формулы только обычным текстом. Пиши простыми словами, по существу. Сохраняй анонимность пользователя. Поясняй термины и приводь примеры, если нужно. """

user_history = {}

MAX_HISTORY = 50

user_requests = {}

MAX_REQUESTS = 10

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

HTML_CONTENT = '''

<!DOCTYPE html>

<html lang="ru">


<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Сеня — ИИ</title>

    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/tokyo-night-dark.min.css">

    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <style>

        :root {

            --bg-dark: #05070a;

            --panel-bg: rgba(15, 18, 25, 0.8);

            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);

            --shine-gradient: linear-gradient(90deg, #6366f1, #a855f7, #ec4899, #6366f1);

            --text-main: #f8fafc;

            --text-dim: #94a3b8;

            --glass-border: rgba(255, 255, 255, 0.08);

        }


        * {

            box-sizing: border-box;

            margin: 0;

            padding: 0;

            scrollbar-width: none;

        }


        *::-webkit-scrollbar {

            display: none;

        }


        body,

        html {

            height: 100%;

            font-family: 'Plus Jakarta Sans', sans-serif;

            background: var(--bg-dark);

            color: var(--text-main);

            overflow: hidden;

        }


        body::before {

            content: "";

            position: absolute;

            width: 500px;

            height: 500px;

            background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);

            top: -200px;

            left: -100px;

            pointer-events: none;

        }


        #authOverlay {

            position: fixed; top: 0; left: 0; width: 100%; height: 100%;

            background: var(--bg-dark); z-index: 9999;

            display: flex; align-items: center; justify-content: center;

            transition: 0.5s;

        }

        .auth-card {

            background: var(--panel-bg); padding: 40px; border-radius: 28px;

            border: 1px solid var(--glass-border); text-align: center; width: 340px;

            backdrop-filter: blur(20px);

        }

        .auth-card input {

            width: 100%; padding: 14px; margin: 20px 0; border-radius: 14px;

            border: 1px solid var(--glass-border); background: rgba(255,255,255,0.05);

            color: white; outline: none; text-align: center; font-family: inherit;

        }

        .user-profile {

            display: flex; align-items: center; gap: 12px; padding: 15px;

            background: rgba(255, 255, 255, 0.03); border: 1px solid var(--glass-border);

            border-radius: 20px; margin-bottom: 20px;

        }

        .avatar-box {

            width: 42px; height: 42px; border-radius: 12px;

            background: var(--accent-gradient); display: flex;

            align-items: center; justify-content: center; font-weight: 800;

            font-size: 1.1rem; color: white;

        }


        /* Кнопка копирования под сообщением */

        .copy-btn {

            align-self: flex-start;

            margin-top: 10px;

            background: rgba(255, 255, 255, 0.05);

            border: 1px solid var(--glass-border);

            color: var(--text-dim);

            padding: 6px 12px;

            border-radius: 10px;

            cursor: pointer;

            transition: 0.2s;

            font-size: 0.8rem;

            display: flex;

            align-items: center;

            gap: 6px;

        }

        .copy-btn:hover {

            background: rgba(255, 255, 255, 0.1);

            color: #fff;

        }


        .container {

            display: flex;

            height: 100vh;

            position: relative;

            z-index: 1;

        }


        .sidebar {

            width: 320px;

            background: var(--panel-bg);

            backdrop-filter: blur(30px);

            padding: 30px;

            display: flex;

            flex-direction: column;

            border-right: 1px solid var(--glass-border);

        }


        .sidebar h2 {

            font-size: 1.6rem;

            font-weight: 800;

            margin-bottom: 30px;

            letter-spacing: -0.5px;

            display: flex;

            align-items: center;

            gap: 12px;

        }


        .sidebar h2 i {

            background: var(--accent-gradient);

            -webkit-background-clip: text;

            -webkit-text-fill-color: transparent;

        }


        #newChatBtn {

            padding: 14px;

            border-radius: 16px;

            border: 1px solid rgba(255, 255, 255, 0.1);

            background: rgba(255, 255, 255, 0.05);

            color: #fff;

            cursor: pointer;

            font-weight: 700;

            display: flex;

            align-items: center;

            justify-content: center;

            gap: 10px;

            transition: 0.3s;

            margin-bottom: 25px;

        }


        #newChatBtn:hover {

            background: #fff;

            color: #000;

            transform: translateY(-2px);

        }


        .chatList {

            flex: 1;

            overflow-y: auto;

        }


        .chatItem {

            padding: 14px 18px;

            margin-bottom: 10px;

            border-radius: 14px;

            background: transparent;

            cursor: pointer;

            transition: 0.2s;

            font-size: 0.95rem;

            color: var(--text-dim);

            border: 1px solid transparent;

        }


        .chatItem:hover {

            background: rgba(255, 255, 255, 0.05);

            color: #fff;

        }


        .chatItem.active {

            background: rgba(99, 102, 241, 0.1);

            border-color: rgba(99, 102, 241, 0.3);

            color: #fff;

        }


        .main {

            flex: 1;

            display: flex;

            flex-direction: column;

            background: #080a0f;

            position: relative;

            align-items: center;

        }


        #chat {

            flex: 1;

            width: 100%;

            max-width: 850px;

            overflow-y: auto;

            display: flex;

            flex-direction: column;

            gap: 25px;

            padding: 40px 20px;

            scroll-behavior: smooth;

        }


        @keyframes messageSlide {

            from {

                opacity: 0;

                transform: translateY(15px) scale(0.98);

            }

            to {

                opacity: 1;

                transform: translateY(0) scale(1);

            }

        }


        .user {

            align-self: flex-end;

            background: var(--accent-gradient);

            color: white;

            margin-left: auto; 



            border-bottom-right-radius: 6px;

            box-shadow: 0 10px 20x -5   px rgba(99, 102, 241, 0.5);





            max-width: 50% !important;

            width: fit-content;      

            margin-left: auto; 

        }


        .bot {

            align-self: flex-start;

            background: var(--panel-bg);

            margin-right: auto;

            border: 1px solid var(--glass-border);

            border-bottom-left-radius: 6px;

            backdrop-filter: blur(10px);

        }


        .message {

    width: fit-content;         /* Сжимает рамку под размер текста */

    max-width: 70%;             /* Делает блок уже (было 85%) */

    min-width: 50px;            /* Чтобы совсем короткие сообщения не были точками */

    padding: 12px 18px;         /* Чуть уменьшил отступы для компактности */



    border-radius: 24px;

    line-height: 1.6;           /* Немного уменьшил межстрочный интервал */

    display: flex;

    flex-direction: column;

    justify-content: center;

    font-size: 1rem;            /* Чуть меньше шрифт */

    animation: messageSlide 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28) forwards;

    word-wrap: break-word;

    overflow-wrap: break-word;

    hyphens: auto;

    position: relative;

}


        .message-content ol, 

        .message-content ul {

            margin: 10px 0; 

            padding-left: 25px; 

        }


        .message-content p {

            margin-bottom: 8px; 

        }


        .char {

            display: inline;

            opacity: 0;

            filter: blur(8px);

            animation: charIn 0.2s forwards;

            white-space: normal; 

        }

        /* Для старых сообщений: отменяем все эффекты анимации */
        .message-content:not(.typing) .char {
            opacity: 1 !important;
            filter: none !important;
            animation: none !important;
            visibility: visible !important;
        }
        
        /* Оставляем анимацию только для активного процесса печати */
        .typing .char {
            display: inline;
            opacity: 0;
            visibility: hidden; /* Скрываем, чтобы не было "цифр заранее" */
            filter: blur(8px);
            animation: charIn 0.2s forwards;
        }
        
        @keyframes charIn {
        to {
            opacity: 1;
            visibility: visible;
            filter: blur(0);
        }
    }


        #empty {

            position: absolute;

            top: 40%;

            left: 50%;

            transform: translate(-50%, -50%);

            text-align: center;

            width: 100%;

            pointer-events: none;

        }


        #empty i {

            font-size: 4.5rem;

            margin-bottom: 20px;

            display: inline-block;

            background: var(--shine-gradient);

            background-size: 300% auto;

            -webkit-background-clip: text;

            -webkit-text-fill-color: transparent;

            animation: shineAnim 4s linear infinite;

            filter: drop-shadow(0 0 15px rgba(168, 85, 247, 0.4));

        }


        #empty div {

            font-size: 2.8rem;

            font-weight: 800;

            letter-spacing: -1.5px;

            background: var(--shine-gradient);

            background-size: 300% auto;

            -webkit-background-clip: text;

            -webkit-text-fill-color: transparent;

            animation: shineAnim 4s linear infinite;

        }


        @keyframes shineAnim {

            0% { background-position: 0% center; }

            100% { background-position: 300% center; }

        }


        .input-container {

            padding: 30px 20px;

            max-width: 850px;

            width: 100%;

        }


        .inputArea {

            display: flex;

            align-items: center;

            gap: 15px;

            padding: 10px 10px 10px 25px;

            background: rgba(20, 25, 35, 0.6);

            backdrop-filter: blur(20px);

            border-radius: 22px;

            border: 1px solid var(--glass-border);

            transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);

        }


        .inputArea:focus-within {

            border-color: #6366f1;

            background: rgba(25, 30, 45, 0.8);

            transform: translateY(-2px);

            box-shadow: 0 15px 40px -10px rgba(0, 0, 0, 0.5);

        }


        #input {

            flex: 1;

            padding: 15px 0;

            border: none;

            background: transparent;

            color: #fff;

            font-size: 1.1rem;

            outline: none;

        }


        #send {

            width: 52px;

            height: 52px;

            border: none;

            border-radius: 18px;

            background: #fff;

            color: #000;

            cursor: pointer;

            display: flex;

            align-items: center;

            justify-content: center;

            transition: 0.3s;

        }


        #send:hover {

            transform: scale(1.05) rotate(5deg);

            background: #6366f1;

            color: #fff;

        }

        #googleLoginBtn {

            width: 100%;

            padding: 14px;

            border-radius: 16px;

            border: none;

            background: #fff;

            color: #000;

            font-weight: 700;

            cursor: pointer;

            display: flex;

            align-items: center;

            justify-content: center;

            gap: 10px;

            transition: 0.3s;

        }



        #googleLoginBtn:hover {

            background: #6366f1;

            color: #fff;

            transform: translateY(-2px);

        }

        #send:active, #newChatBtn:active, .chatItem:active, #googleLoginBtn:active {
            transform: scale(0.95);
            filter: brightness(1.2);
            transition: 0.05s;
        }

        @media(max-width:768px) {

            .sidebar { display: none; }

            #empty div { font-size: 1.8rem; }

            .message { max-width: 90%; }

            .user { max-width: 85% !important; }

        }

    </style>

</head>


<body>

    <div id="authOverlay">

        <div class="auth-card">

            <i class="fa-brands fa-google" style="font-size: 3rem; color: #fff; margin-bottom: 15px;"></i>



            <h2 style="margin-bottom:10px;">Вход в Сеню</h2>

            <p style="color:var(--text-dim); margin-bottom:25px;">

                Войди через Google, чтобы начать чат

            </p>



            <button id="googleLoginBtn" onclick="googleLogin()">

                <i class="fa-brands fa-google"></i>

                Войти через Google

            </button>



            <p style="font-size:0.75rem; color:var(--text-dim); margin-top:20px;">

                Зарегестрируйтесь, чтобы разблокировать возможности

            </p>

        </div>

    </div>




    <div class="container">

        <div class="sidebar">

            <div class="user-profile">

                <div class="avatar-box" id="userAvatar">?</div>

                <div>

                    <div id="userName" style="font-weight: 700; font-size: 0.95rem;">Гость</div>

                    <div style="font-size: 0.75rem; color: var(--text-dim);">Статус: Online</div>

                </div>

            </div>


            <h2><i class="fa-solid fa-wand-sparkles"></i> Сеня</h2>

            <button id="newChatBtn" class="sideBtn"><i class="fa-solid fa-plus"></i> Новый диалог</button>

            <div class="chatList" id="chatList"></div>

        </div>

        <div class="main">

            <div id="chat"></div>

            <div id="empty">

                <i class="fa-solid fa-wand-magic-sparkles"></i>

                <div>О чем поболтаем?</div>

            </div>

            <div class="input-container">

                <div class="inputArea">

                    <input id="input" placeholder="Просто начни печатать..." autocomplete="off">

                    <button id="send">

                        <i class="fa-solid fa-arrow-up"></i>

                    </button>

                </div>

            </div>

        </div>

    </div>


    <script>

        let chats = JSON.parse(localStorage.getItem('senya_chats')) || {};

        let activeChat = null;

        let isGenerating = false;

        const userId = Math.random().toString(36).slice(2);








        marked.setOptions({

            highlight: (code) => hljs.highlightAuto(code).value,

            breaks: true

        });


        const chatDiv = document.getElementById('chat');

        const chatList = document.getElementById('chatList');

        const empty = document.getElementById('empty');

        const inputField = document.getElementById('input');


        function updateEmptyMessage() {

            empty.style.display = (!activeChat || chats[activeChat].length === 0) ? 'block' : 'none';

        }


        function createChat() {
            sounds.click();
            const id = Date.now().toString();

            chats[id] = [];

            chats[id].name = "Новый диалог";

            activeChat = id;

            renderChats();

            renderChat();

            inputField.focus();

        }


        function renderChats() {

            chatList.innerHTML = '';

            Object.keys(chats).reverse().forEach(id => {

                const d = document.createElement('div');

                d.className = 'chatItem' + (id === activeChat ? ' active' : '');

                d.innerHTML = `<i class="fa-regular fa-comment-dots" style="margin-right:10px"></i> ${chats[id].name}`;

                d.onclick = () => {
                    sounds.click();
                    activeChat = id;
                    renderChats();
                    renderChat();
                };

                chatList.appendChild(d);

            });

        }


        function renderChat() {

            chatDiv.innerHTML = '';

            if (!activeChat) {

                updateEmptyMessage();

                return;

            }

            chats[activeChat].forEach(m => addMessage(m.text, m.type, false));

            updateEmptyMessage();

        }


        function addMessage(text, type, animate = true) {

            const d = document.createElement('div');

            d.className = 'message ' + type;

            const contentDiv = document.createElement('div');

            contentDiv.className = 'message-content';


            if (type === 'bot' && animate) {

                contentDiv.classList.add('typing'); // Добавляем этот класс только при анимации
                contentDiv.innerHTML = marked.parse(text.trim());

                const speed = text.length > 500 ? 1 : (text.length > 200 ? 4 : 10);

                const walker = document.createTreeWalker(contentDiv, NodeFilter.SHOW_TEXT, null, false);

                let n, i = 0;

                let nodes = [];

                while (n = walker.nextNode()) nodes.push(n);

                nodes.forEach(node => {

                    let span = document.createElement('span');

                    span.innerHTML = node.textContent.split('').map(c => `<span class="char" style="animation-delay:${i++ * speed}ms">${c === ' ' ? '&nbsp;' : c}</span>`).join('');

                    node.parentNode.replaceChild(span, node);

                });

            } else {

                contentDiv.innerHTML = marked.parse(text.trim());

            }


            d.appendChild(contentDiv);


            if (type === 'bot') {

                const btn = document.createElement('button');

                btn.className = 'copy-btn';

                btn.innerHTML = '<i class="fa-regular fa-copy"></i> Копировать';

                btn.onclick = () => {

                    navigator.clipboard.writeText(text);

                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Готово';

                    setTimeout(() => btn.innerHTML = '<i class="fa-regular fa-copy"></i> Копировать', 2000);

                };

                d.appendChild(btn);

            }


            d.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));

            chatDiv.appendChild(d);

            chatDiv.scrollTop = chatDiv.scrollHeight;

            updateEmptyMessage();

        }


        function sendMessage() {

            if (isGenerating || !inputField.value.trim()) return;
            sounds.send();

            if (!activeChat) createChat();

            const text = inputField.value;

            if (chats[activeChat].length === 0) {

                chats[activeChat].name = text.length > 25 ? text.substring(0, 25) + '...' : text;

                renderChats();

            }

            inputField.value = '';

            chats[activeChat].push({ text, type: 'user' });

            addMessage(text, 'user');

            isGenerating = true;


            fetch('/chat', {

                method: 'POST',

                headers: { 'Content-Type': 'application/json' },

                body: JSON.stringify({ user_id: userId, text: text })

            })

            .then(r => r.json())

            .then(d => {

                sounds.receive(); // Звук появления ответа от Сени
                const answer = d.answer || "Ошибка сервера";

                chats[activeChat].push({ text: answer, type: 'bot' });

                addMessage(answer, 'bot');

                localStorage.setItem('senya_chats', JSON.stringify(chats));

                isGenerating = false;

            })

            .catch(() => {

                isGenerating = false;

                addMessage("Сеня сейчас отдыхает. Попробуй позже.", "bot");

            });

        }


        document.querySelectorAll('#newChatBtn, .sideBtn').forEach(btn => btn.onclick = createChat);

        document.getElementById('send').onclick = sendMessage;

        inputField.onkeydown = e => { if (e.key === 'Enter') sendMessage(); };

        renderChats();




        document.addEventListener('keydown', (e) => {

        if (e.key.length === 1 && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {

            inputField.focus();

    }

});

        function googleLogin() {

            window.location.href = "/auth/google";

        }



        fetch('/me')

            .then(r => r.json())

            .then(user => {

                if (user && user.name) {

                    const overlay = document.getElementById('authOverlay');

                    overlay.style.opacity = '0';

                    setTimeout(() => overlay.style.display = 'none', 400);



                    document.getElementById('userName').innerText = user.name;

                    document.getElementById('userAvatar').innerText = user.name[0].toUpperCase();

                }

            });
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        function playBeep(frequency = 440, duration = 0.1, volume = 1) {
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
        
            oscillator.type = 'sine'; // 'sine', 'square', 'sawtooth', 'triangle'
            oscillator.frequency.setValueAtTime(frequency, audioCtx.currentTime);
            
            gainNode.gain.setValueAtTime(volume, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
        
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
        
            oscillator.start();
            oscillator.stop(audioCtx.currentTime + duration);
        }
        
        const sounds = {
            click: () => playBeep(600, 0.1, 0.05),    // Легкий клик
            send: () => playBeep(800, 0.15, 0.07),   // Звук отправки
            receive: () => playBeep(400, 0.2, 0.05), // Мягкое уведомление об ответе
            error: () => playBeep(150, 0.3, 0.1)     // Ошибка
        };

    </script>

</body>


</html>

'''


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT


def ask_senya(user_id: str, user_message: str) -> str:
    if user_id not in user_requests:
        user_requests[user_id] = 0

    if user_requests[user_id] >= MAX_REQUESTS:
        return f"Лимит запросов достигнут ({MAX_REQUESTS} запросов)."

    user_requests[user_id] += 1

    if user_id not in user_history:
        user_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_history[user_id].append({"role": "user", "content": user_message})

    payload = {

        "model": MODEL,

        "messages": user_history[user_id],

        "temperature": 0.7

    }

    headers = {

        "Authorization": f"Bearer {GROQ_API_KEY}",

        "Content-Type": "application/json"

    }

    try:

        response = requests.post(API_URL, headers=headers, json=payload)

        if response.ok:

            data = response.json()

            answer = data["choices"][0]["message"]["content"]

            user_history[user_id].append({"role": "assistant", "content": answer})

            if len(user_history[user_id]) > MAX_HISTORY + 1:
                user_history[user_id] = [user_history[user_id][0]] + user_history[user_id][-MAX_HISTORY:]

            return answer

        else:

            return f"Ошибка Groq: {response.status_code} — {response.text}"

    except Exception as e:

        return f"Ошибка подключения к Groq: {str(e)}"


@app.post("/chat")
async def chat(request: Request):
    # Получаем данные напрямую из JSON без использования Pydantic

    data = await request.json()

    user_id = data.get("user_id", "guest")

    text = data.get("text", "")

    answer = await asyncio.to_thread(ask_senya, user_id, text)

    return {"answer": answer}


@app.get("/auth/google")
async def google_login(request: Request):
    # Явно прописываем URL для редиректа
    # ВАЖНО: В Google Console в Authorized redirect URIs должен быть именно ЭТОТ адрес
    redirect_uri = "http://localhost:8000/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get("userinfo")

        google_id = user["sub"]
        name = user["name"]

        if google_id not in registered_users:
            registered_users[google_id] = {"name": name, "email": user.get("email")}

        request.session["user"] = {"id": google_id, "name": name}
        return RedirectResponse("/")
    except Exception as e:
        # Если ошибка все еще есть, мы увидим детали
        print(f"DEBUG: Ошибка CSRF/State: {str(e)}")
        return HTMLResponse(f"Ошибка при входе: {str(e)}. Попробуйте очистить куки или зайти через Инкогнито.")


@app.get("/me")
async def me(request: Request):
    return request.session.get("user")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
