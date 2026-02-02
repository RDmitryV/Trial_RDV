<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { ChatMessage } from '@/stores/chat'

import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import ScrollPanel from 'primevue/scrollpanel'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  researchId: string
  enableStreaming?: boolean
}>()

const chatStore = useChatStore()
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const isLoading = ref(false)

// Set active research and connect WebSocket if streaming is enabled
onMounted(async () => {
  chatStore.setActiveResearch(props.researchId)

  if (props.enableStreaming) {
    try {
      await chatStore.connectWebSocket(props.researchId)
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }
})

onUnmounted(() => {
  if (props.enableStreaming) {
    chatStore.disconnectWebSocket(props.researchId)
  }
})

const conversation = computed(() => chatStore.getConversation(props.researchId))
const messages = computed(() => conversation.value.messages)
const isStreaming = computed(() => conversation.value.isStreaming)
const error = computed(() => conversation.value.error)

const sendMessage = async () => {
  const message = messageInput.value.trim()
  if (!message || isLoading.value || isStreaming.value) return

  try {
    isLoading.value = true

    if (props.enableStreaming && conversation.value.isConnected) {
      // Use WebSocket for streaming
      chatStore.sendWebSocketMessage(props.researchId, message)
    } else {
      // Use HTTP API
      await chatStore.sendMessage(props.researchId, message)
    }

    messageInput.value = ''

    // Scroll to bottom
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to send message:', error)
  } finally {
    isLoading.value = false
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    const scrollPanel = messagesContainer.value.querySelector('.p-scrollpanel-content')
    if (scrollPanel) {
      scrollPanel.scrollTop = scrollPanel.scrollHeight
    }
  }
}

const renderMarkdown = (content: string): string => {
  const html = marked(content)
  return DOMPurify.sanitize(html as string)
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getToolLabel = (toolName: string): string => {
  const labels: Record<string, string> = {
    search_web: 'Поиск в интернете',
    parse_url: 'Парсинг страницы',
    search_companies: 'Поиск компаний',
    get_statistics: 'Получение статистики',
    analyze_sentiment: 'Анализ тональности',
  }
  return labels[toolName] || toolName
}
</script>

<template>
  <Card class="ai-chat-panel h-full">
    <template #title>
      <div class="flex justify-content-between align-items-center">
        <div class="flex align-items-center gap-2">
          <i class="pi pi-comments text-2xl"></i>
          <span>AI-ассистент</span>
        </div>
        <Tag
          v-if="enableStreaming && conversation.isConnected"
          severity="success"
          value="Подключено"
          icon="pi pi-circle-fill"
        />
      </div>
    </template>

    <template #content>
      <div class="flex flex-column gap-3 h-full">
        <!-- Error message -->
        <Message v-if="error" severity="error" :closable="false">
          {{ error }}
        </Message>

        <!-- Messages -->
        <ScrollPanel
          ref="messagesContainer"
          class="flex-1"
          style="height: 400px"
        >
          <div class="flex flex-column gap-3 pr-3">
            <!-- Welcome message -->
            <div v-if="messages.length === 0" class="text-center py-5">
              <i class="pi pi-comments text-5xl text-400 mb-3"></i>
              <p class="text-xl mb-2">Добро пожаловать!</p>
              <p class="text-600">
                Задайте вопрос по исследованию, и я помогу найти ответ.
              </p>
            </div>

            <!-- Chat messages -->
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="flex"
              :class="msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'"
            >
              <div
                class="message-bubble p-3 border-round-lg max-w-30rem"
                :class="msg.role === 'user' ? 'bg-primary text-white' : 'surface-100'"
              >
                <!-- Message content -->
                <div
                  v-if="msg.role === 'user'"
                  class="text-white"
                >
                  {{ msg.content }}
                </div>
                <div
                  v-else
                  class="markdown-content"
                  v-html="renderMarkdown(msg.content)"
                ></div>

                <!-- Tool uses -->
                <div v-if="msg.tool_uses && msg.tool_uses.length > 0" class="mt-2">
                  <div class="flex flex-wrap gap-1">
                    <Tag
                      v-for="(tool, toolIndex) in msg.tool_uses"
                      :key="toolIndex"
                      severity="info"
                      :value="getToolLabel(tool.tool)"
                      icon="pi pi-wrench"
                      class="text-xs"
                    />
                  </div>
                </div>

                <!-- Timestamp -->
                <div class="text-xs mt-2 opacity-70">
                  {{ formatTime(msg.timestamp) }}
                </div>
              </div>
            </div>

            <!-- Streaming indicator -->
            <div v-if="isStreaming" class="flex justify-content-start">
              <div class="message-bubble p-3 border-round-lg surface-100">
                <i class="pi pi-spin pi-spinner"></i>
                <span class="ml-2">Печатаю...</span>
              </div>
            </div>
          </div>
        </ScrollPanel>

        <!-- Input -->
        <div class="flex gap-2">
          <InputText
            v-model="messageInput"
            placeholder="Введите сообщение..."
            class="flex-1"
            @keyup.enter="sendMessage"
            :disabled="isLoading || isStreaming"
          />
          <Button
            icon="pi pi-send"
            @click="sendMessage"
            :loading="isLoading"
            :disabled="!messageInput.trim() || isStreaming"
          />
        </div>

        <!-- Helper text -->
        <div class="text-xs text-600">
          Вы можете спросить о данных исследования, попросить уточнить параметры или запустить анализ.
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.ai-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.message-bubble {
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.markdown-content :deep(p) {
  margin: 0.5rem 0;
}

.markdown-content :deep(p:first-child) {
  margin-top: 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: rgba(0, 0, 0, 0.05);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}
</style>
