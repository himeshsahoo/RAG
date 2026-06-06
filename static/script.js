document.addEventListener('DOMContentLoaded', () => {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const statusIndicator = document.getElementById('status-indicator');
    const activeDoc = document.getElementById('active-doc');
    const docName = document.getElementById('doc-name');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatForm = document.getElementById('chat-form');
    const chatContainer = document.getElementById('chat-container');

    // Handle File Selection
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = 'rgba(79, 172, 254, 1)';
        uploadZone.style.background = 'rgba(79, 172, 254, 0.15)';
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.style.borderColor = '';
        uploadZone.style.background = '';
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = '';
        uploadZone.style.background = '';
        
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    async function handleFileUpload(file) {
        if (!file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
            alert('Please upload a PDF or TXT file.');
            return;
        }

        setStatus('Processing document...', 'loading');
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                setStatus('Model Status: Ready & Contextualized', 'success');
                activeDoc.classList.remove('hidden');
                docName.textContent = file.name;
                
                chatInput.disabled = false;
                sendBtn.disabled = false;
                chatInput.focus();
                
                // Clear chat
                chatContainer.innerHTML = '';
            } else {
                const err = await response.json();
                setStatus(`Error: ${err.detail || 'Upload failed'}`, 'error');
            }
        } catch (error) {
            setStatus('Error uploading file.', 'error');
        }
    }

    function setStatus(text, type) {
        statusIndicator.textContent = text;
        statusIndicator.className = `status-indicator ${type === 'success' ? 'success' : 'error'}`;
        if(type === 'loading') {
            statusIndicator.style.background = 'rgba(79, 172, 254, 0.1)';
            statusIndicator.style.color = 'var(--accent-2)';
        } else {
            statusIndicator.style.background = '';
            statusIndicator.style.color = '';
        }
    }

    // Chat Logic
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        chatInput.value = '';
        
        const typingId = showTypingIndicator();
        chatInput.disabled = true;
        sendBtn.disabled = true;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            removeTypingIndicator(typingId);
            
            if (response.ok) {
                appendMessage(data.answer, 'assistant', data.is_cloud);
            } else {
                appendMessage('Error: ' + (data.detail || 'Failed to get answer.'), 'assistant');
            }
        } catch (error) {
            removeTypingIndicator(typingId);
            appendMessage('Network error. Please try again.', 'assistant');
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    });

    function appendMessage(text, sender, isCloud = false) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        if (isCloud) msgDiv.classList.add('cloud');
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        // Simple markdown handling for bold
        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        if (isCloud) {
            formattedText = `🌩️ <em>(Cloud Fallback with Context)</em><br><br>${formattedText}`;
        }
        
        contentDiv.innerHTML = formattedText;
        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.id = id;
        indicator.classList.add('typing-indicator');
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatContainer.appendChild(indicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) indicator.remove();
    }
});
