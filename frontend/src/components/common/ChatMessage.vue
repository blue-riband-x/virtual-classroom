<template>
  <div class="chat-message" :class="message.type">
    <div class="message-avatar" v-if="message.type === 'ai' || message.type === 'classmate'">
      {{ message.avatar || '🤖' }}
    </div>
    <div class="message-content">
      <div class="message-header" v-if="message.type === 'ai' || message.type === 'classmate'">
        <span class="message-sender">{{ message.sender }}</span>
        <span class="message-time">{{ message.timestamp }}</span>
      </div>
      <div class="message-bubble">
        <div v-if="message.type === 'ai' && message.isTyping" class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <template v-else>
          {{ message.content }}
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  animation: messageIn 0.3s ease;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 50%;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.message-sender {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
}

.message-time {
  font-size: 0.625rem;
  color: var(--text-muted);
}

.message-bubble {
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  line-height: 1.5;
  font-size: 0.875rem;
}

.chat-message.ai .message-bubble,
.chat-message.classmate .message-bubble {
  background: var(--bg-secondary);
  border-bottom-left-radius: 4px;
}

.chat-message.user .message-bubble {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-message.classmate .message-bubble {
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.5rem;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>
