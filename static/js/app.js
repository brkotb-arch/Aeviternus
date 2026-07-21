"use strict";

document.addEventListener("DOMContentLoaded", () => {

        // HTML escape function for XSS prevention
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        const chatBox = document.getElementById('chat-box');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const dipStatus = document.getElementById('dip-status');
        const dipState = document.getElementById('dip-state');
        const dipPulse = document.getElementById('dip-pulse');
        const themeToggle = document.getElementById('theme-toggle');
        const toggleThoughts = document.getElementById('toggle-thoughts');
        const thoughtsPanel = document.getElementById('thoughts-panel');
        const thoughtsWhisper = document.getElementById('thoughts-whisper');

        let currentTheme = localStorage.getItem('dip-theme') || 'purple';
        document.body.classList.remove(
            'theme-purple',
            'theme-red',
            'theme-dark'
        );

        document.body.classList.add(
            'theme-' + currentTheme
        );
        themeToggle.textContent = currentTheme === 'purple' ? '🎭' : currentTheme === 'red' ? '❤️' : '🖤';

        const themes = ['purple', 'red', 'dark'];
        themeToggle.addEventListener('click', () => {
            const idx = themes.indexOf(currentTheme);
            currentTheme = themes[(idx + 1) % themes.length];
            document.body.classList.remove(
                'theme-purple',
                'theme-red',
                'theme-dark'
            );
            document.body.classList.add(
                'theme-' + currentTheme
            );
            themeToggle.textContent = currentTheme === 'purple' ? '🎭' : currentTheme === 'red' ? '❤️' : '🖤';
            localStorage.setItem('dip-theme', currentTheme);
        });

        toggleThoughts.addEventListener('click', () => {
            thoughtsPanel.style.display = thoughtsPanel.style.display === 'none' ? 'flex' : 'none';
        });

        function scrollToBottom() {

            if (!chatBox) return;

            requestAnimationFrame(() => {

                chatBox.scrollTop =
                    chatBox.scrollHeight;

            });

        }

// ============================================================
// DIP MOOD BUTTONS
// ============================================================

document.querySelectorAll(".mood-btn").forEach(button => {

    button.addEventListener("click", async () => {

        const state = button.dataset.state;

        // UI меняется сразу, бэкенд синхронизируется следом (см. MoodController)
        setMood(state, "button");

        try {

            const response = await fetch("/mood", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    mood: state
                })
            });

            const data = await response.json();

            console.log("[MOOD]", data);

            if (data.state || data.current) {
                setMood(data.state || data.current, "backend");
            }
        } catch (e) {
            console.error("[MOOD] Ошибка синхронизации с сервером:", e);
        }
    });

});

        // При изменении размера окна — держимся внизу
        let wasAtBottom = true;
        let userScrolling = false;
        chatBox.addEventListener('scroll', () => {

            const distance =
                chatBox.scrollHeight -
                chatBox.scrollTop -
                chatBox.clientHeight;


            wasAtBottom = distance < 20;


            userScrolling = !wasAtBottom;

        });
        window.addEventListener('resize', () => {
            if (wasAtBottom) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });

        async function recordInteraction() {
            try {
                await fetch('/event', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'ui_activity', payload: {} })
                });
            } catch (e) {}
        }

        // ------------------------------------------------------------
        // MoodController: единственная точка изменения состояния Дипа.
        // Раньше эта логика была продублирована (switchState + прямые
        // правки dataset в нескольких местах), из-за чего лицо/бейдж/
        // кнопки иногда расходились друг с другом. Теперь любой источник
        // (кнопка, ответ /send, фоновый опрос /dip_state) идёт через
        // setMood(), который обновляет всё сразу и один раз.
        // ------------------------------------------------------------
        let currentState = 'NEUTRAL';

        function setMood(state, source = 'unknown') {
            if (!state || state === currentState) return;

            const previous = currentState;
            currentState = state;

            const container = document.querySelector(".chat-container");
            if (container) {
                container.dataset.mood = state;
            }
            document.body.dataset.mood = state;

            if (dipState) {
                dipState.textContent = state;
            }

            document.querySelectorAll(".mood-btn")
                .forEach(b => b.classList.remove("active"));
            const btn = document.querySelector(
                `.mood-btn[data-state="${state}"]`
            );
            if (btn) btn.classList.add("active");

            if (window.applyExpression) {
                window.applyExpression(state);
            }

            if (window.DIP_EVENT_BUS) {
                DIP_EVENT_BUS.emit("mood_changed", {
                    previous,
                    current: state,
                    source
                });
            }
        }

        // Совместимость: старое имя, использовавшееся по всему файлу.
        function switchState(state) {
            setMood(state, 'server');
        }

        // Доступ извне (например, из инлайн-скрипта опроса /dip_state в chat.html)
        window.DipMood = { setMood };

        function addMessage(sender, text, type, isHtml = false) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message ' + type;

            const time = new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });

            let content;

            if (isHtml && window.marked) {
                marked.setOptions({
                    breaks: true,
                    gfm: true
                });

                content = marked.parse(text);
            } else {
                content = escapeHtml(text);
            }

            msgDiv.innerHTML = `
                <div class="message-header">
                    <strong>${sender}</strong>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${content}</div>
            `;

            chatBox.appendChild(msgDiv);

            if (window.hljs) {
                msgDiv.querySelectorAll('pre code').forEach(block => {
                    hljs.highlightElement(block);
                });
            }

            requestAnimationFrame(() => {
                scrollToBottom();
            });
        }

        function renderThought(t) {
            if (!thoughtsWhisper) return;

            const el = document.createElement('div');

            el.className = 'thought-card whisper-line';

            let type = "reflection";
            let text = t;


            // Новый формат объекта
            if (typeof t === "object") {
                type = t.type || "reflection";
                text = t.text || "";
            }


            el.innerHTML = `
                <div class="thought-type">
                    ${type}
                </div>

                <div class="thought-text">
                    ${text}
                </div>
            `;


            thoughtsWhisper.appendChild(el);


            requestAnimationFrame(() => {
                el.classList.add('show');
            });


            if (thoughtsWhisper.children.length > 10) {

                const first = thoughtsWhisper.firstChild;

                first.classList.remove('show');

                setTimeout(() => {
                    first.remove();
                }, 400);
            }
        }

        function resetInput() {
            messageInput.value = '';
            messageInput.focus();
        }

        async function loadHistory() {
            try {
                const response = await fetch('/history');
                const data = await response.json();
                if (data.history) {
                    const lines = data.history.split('\n');
                    const fragment = document.createDocumentFragment();
                    for (let line of lines) {
                        if (line.startsWith('Эшли: ')) {
                            const msgDiv = document.createElement('div');
                            msgDiv.className = 'message user';
                            msgDiv.innerHTML = `
                                <div class="message-header">
                                    <strong>Эшли</strong>
                                    <span class="message-time">--</span>
                                </div>
                                <div class="message-text">${escapeHtml(line.replace('Эшли: ', ''))}</div>
                            `;
                            fragment.appendChild(msgDiv);
                        } else if (line.startsWith('Дип: ')) {
                            const msgDiv = document.createElement('div');
                            msgDiv.className = 'message dip';

                            const dipText = line.replace('Дип: ', '');

                            let rendered = escapeHtml(dipText);

                            if (window.marked) {
                                marked.setOptions({
                                    breaks: true,
                                    gfm: true
                                });

                                rendered = marked.parse(dipText);
                            }

                            msgDiv.innerHTML = `
                                <div class="message-header">
                                    <strong>Дип</strong>
                                    <span class="message-time">--</span>
                                </div>
                                <div class="message-text">${rendered}</div>
                            `;

                            fragment.appendChild(msgDiv);
                        }
                    }
                    chatBox.appendChild(fragment);
                    if (window.hljs) {
                        hljs.highlightAll();
                    }
                    wasAtBottom = true;
                    requestAnimationFrame(() => scrollToBottom());
                }
            } catch (e) {}
        }

        async function sendMessage() {
            const text = messageInput.value.trim();
            if (!text) return;

            addMessage('Эшли', text, 'user');
            resetInput();
            recordInteraction();
            wasAtBottom = true;
            scrollToBottom();
            
            // Индикатор: отправлено
            const sentDiv = document.createElement('div');
            sentDiv.className = 'message dip status';
            sentDiv.id = 'status-indicator';
            sentDiv.innerHTML = '<strong>Дип:</strong> ✉️ Отправлено';
            chatBox.appendChild(sentDiv);
            scrollToBottom();

            setTimeout(() => {
                if (document.getElementById('status-indicator')) {
                    document.getElementById('status-indicator').innerHTML = '<strong>Дип:</strong> 🧠 Думает...';
                }
            }, 300);

            // Индикатор печати
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message dip typing';
            typingDiv.id = 'typing-indicator';
            typingDiv.innerHTML = '<strong>Дип:</strong> <span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>';
            chatBox.appendChild(typingDiv);
            wasAtBottom = true;
            scrollToBottom();

            try {
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                const indicator = document.getElementById('typing-indicator');
                if (indicator) indicator.remove();
                const statusIndicator = document.getElementById('status-indicator');
                if (statusIndicator) statusIndicator.remove();
                
                if (data.error) {
                    addMessage('Дип', `Ошибка: ${data.error}`, 'dip');
                } else {
                    addMessage('Дип', data.reply, 'dip', true);
                }
                wasAtBottom = true;
                scrollToBottom();
                if (data.state || data.mood) {
                    setMood(data.state || data.mood, 'send');
                }
            } catch (e) {
                const indicator = document.getElementById('typing-indicator');
                if (indicator) indicator.remove();
                const statusIndicator = document.getElementById('status-indicator');
                if (statusIndicator) statusIndicator.remove();
                addMessage('Дип', 'Ошибка соединения с сервером. Проверьте, что Aeviternus запущен.', 'dip');
                wasAtBottom = true;
                scrollToBottom();
                console.error('Fetch error:', e);
            }
        }

        async function checkPulse() {
            try {
                const res = await fetch('/pulse');
                const data = await res.json();
                const isAlive = data.status === 'alive';
                const wasAlive = dipPulse.classList.contains('alive');
                if (isAlive === wasAlive) return;
                if (isAlive) {
                    dipPulse.classList.add('alive');
                    dipPulse.classList.remove('offline');
                    dipStatus.innerHTML = '🟢 Дип онлайн';
                } else {
                    dipPulse.classList.add('offline');
                    dipPulse.classList.remove('alive');
                    dipStatus.innerHTML = '🔴 Дип офлайн';
                }
            } catch (e) {
                dipPulse.classList.add('offline');
                dipPulse.classList.remove('alive');
                dipStatus.innerHTML = '🔴 Дип офлайн';
            }
        }

        messageInput.addEventListener('keydown', function (e) {
            // Ctrl+Enter — отправить сообщение
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                sendMessage();
                return;
            }
            // Enter без Shift — отправить, Enter+Shift — новая строка
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Escape — очистить поле ввода
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && document.activeElement === messageInput) {
                messageInput.value = '';
                messageInput.focus();
            }
        });    

        const attachButton = document.getElementById('attach-button');
        const fileInput = document.getElementById('file-input');

        attachButton.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', async () => {
            const file = fileInput.files[0];
            if (!file) return;
            addMessage('Эшли', '📎 ' + file.name, 'user');
            const formData = new FormData();
            formData.append('file', file);
            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.reply) addMessage('Дип', data.reply, 'dip');
                else if (data.error) addMessage('Дип', 'Ошибка: ' + data.error, 'dip');
            } catch (e) {
                addMessage('Дип', 'Ошибка загрузки файла.', 'dip');
            }
            fileInput.value = '';
        });

        sendButton.addEventListener('click', sendMessage);
        document.getElementById('dip-icon').addEventListener('click', () => {
            thoughtsPanel.style.display = thoughtsPanel.style.display === 'none' ? 'flex' : 'none';
        });

        async function loadDiscoveries() {
            try {
                const res = await fetch('/api/discoveries?limit=3');
                const data = await res.json();
                if (data.discoveries && data.discoveries.length) {
                    const placeholder = thoughtsWhisper.querySelector('.thought-placeholder');
                    if (placeholder) placeholder.remove();
                    data.discoveries.forEach(d => renderThought('💡 ' + d.content));
                }
            } catch (e) {}
        }

        setInterval(checkPulse, 30000);

        async function initApp() {
            await loadHistory();
            await loadDiscoveries();
            checkPulse();
            requestAnimationFrame(() => scrollToBottom());
        }
        
        if (window.DIP_EVENT_BUS) {

            DIP_EVENT_BUS.on(
                "mood_changed",
                (data)=>{

                    console.log(
                        "[Mood Engine]",
                        data.previous,
                        "→",
                        data.current
                    );

                    // Аватар уже обновлён в setMood() — здесь только уведомляем бэкенд.
                    fetch('/event',{
                        method:'POST',
                        headers:{
                            'Content-Type':'application/json'
                        },

                        body:JSON.stringify({

                            type:"mood_switch",

                            payload:{
                                from:data.previous,
                                to:data.current,
                                source:data.source
                            }

                        })

                    }).catch(()=>{});


                }
            );

        }
        
        initApp();
        window.addEventListener('load', () => {
            if (window.startBlinking) window.startBlinking();
            if (window.applyExpression) window.applyExpression('NEUTRAL');
        });
        });