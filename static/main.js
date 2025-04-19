document.addEventListener("DOMContentLoaded", () => {
    const sessionIdInput = document.getElementById("sessionId");
    const messageInput = document.getElementById("userMessage");
    const chatContainer = document.getElementById("chat");
    const sessionsContainer = document.getElementById("sessionsContainer");
    const newChatBtn = document.getElementById("newChatBtn");
    
    let currentSessionId = null; // Track current session for ongoing messages
  
    function clearChat() {
      chatContainer.innerHTML = "";
    }
  
    function displayMessage(role, content) {
      const div = document.createElement("div");
      div.className = `message ${role}`;
      div.innerHTML = `<strong>${role}: </strong>${content}`;
      chatContainer.appendChild(div);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  
    function loadSession(sessionId) {
      fetch(`/session/${encodeURIComponent(sessionId)}`)
        .then(res => res.json())
        .then(messages => {
          console.log('Loaded messages:', messages); // Debug
          clearChat();
          messages.forEach(msg => {
            displayMessage(msg.role, msg.content);
          });
        })
        .catch(error => {
          console.error('Error loading session:', error);
        });
    }
  
    function loadSessions() {
        return fetch('/sessions')
          .then(res => res.json())
          .then(sessions => {
            // Clear previous list to avoid duplicates
            sessionsContainer.innerHTML = "";
      
            sessions.forEach(sessionId => {
              const sessionDiv = document.createElement('div');
              sessionDiv.className = 'session-item';
      
              // Session name (wraps long names)
              const nameSpan = document.createElement('span');
              nameSpan.className = 'session-name';
              nameSpan.textContent = sessionId;
      
              // Container for delete/rename icons
              const actionsDiv = document.createElement('div');
              actionsDiv.className = 'session-actions';
      
              // Delete icon
              const deleteBtn = document.createElement('button');
              deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
              deleteBtn.title = 'Delete session';
              deleteBtn.onclick = () => {
                fetch(`/session/${sessionId}`, { method: 'DELETE' })
                  .then(() => loadSessions());
              };
      
              // Rename icon
              const renameBtn = document.createElement('button');
              renameBtn.innerHTML = '<i class="fas fa-edit"></i>';
              renameBtn.title = 'Rename session';
              renameBtn.onclick = () => {
                const newName = prompt('Enter new session name:', sessionId);
                if (newName) {
                  fetch('/rename-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_id: sessionId, new_id: newName })
                  })
                  .then(res => res.json())
                  .then(data => {
                    if (data.status === 'success') {
                      loadSessions(); // refresh list
                      if (sessionId === currentSessionId) {
                        currentSessionId = newName;
                        sessionIdInput.value = newName;
                        loadSession(newName);
                      }
                    } else {
                      alert('Rename failed: ' + data.error);
                    }
                  });
                }
              };
      
              // Append icons to actions container
              actionsDiv.appendChild(deleteBtn);
              actionsDiv.appendChild(renameBtn);
      
              // Append name and icons to session box
              sessionDiv.appendChild(nameSpan);
              sessionDiv.appendChild(actionsDiv);
      
              // Load session on click
              sessionDiv.onclick = () => {
                sessionIdInput.value = sessionId;
                currentSessionId = sessionId;
                loadSession(sessionId);
              };
      
              sessionsContainer.appendChild(sessionDiv);
            });
      
            // Auto-select the first session if available
            if (sessions.length > 0) {
              const firstSessionId = sessions[0];
              sessionIdInput.value = firstSessionId;
              currentSessionId = firstSessionId;
              loadSession(firstSessionId);
            }
          });
    }
  
    function sendMessage() {
      const message = messageInput.value.trim();
      if (!message || !currentSessionId) return;
  
      fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, prompt: message })
      })
      .then(res => res.json())
      .then(data => {
        displayMessage('user', message);
        displayMessage('assistant', data.response);
        loadSession(currentSessionId);
      });
  
      messageInput.value = '';
    }
  
    document.getElementById('userMessage').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  
    // Handle "New Chat" button
    newChatBtn.addEventListener('click', () => {
      const newSessionId = `session-${Date.now()}`;
      fetch('/session/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: newSessionId })
      }).then(() => {
        loadSessions().then(() => {
          sessionIdInput.value = newSessionId;
          currentSessionId = newSessionId;
          loadSession(newSessionId);
        });
      });
    });
  
    // Load all sessions initially
    loadSessions();
  });