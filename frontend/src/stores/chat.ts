import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  tool_uses?: Array<{
    tool: string
    arguments: Record<string, any>
    result?: any
    error?: string
  }>
}

export interface ChatState {
  messages: ChatMessage[]
  isConnected: boolean
  isStreaming: boolean
  error: string | null
}

export const useChatStore = defineStore('chat', () => {
  // State
  const conversations = ref<Map<string, ChatState>>(new Map())
  const activeResearchId = ref<string | null>(null)
  const websockets = ref<Map<string, WebSocket>>(new Map())

  // Getters
  const getConversation = (researchId: string): ChatState => {
    if (!conversations.value.has(researchId)) {
      conversations.value.set(researchId, {
        messages: [],
        isConnected: false,
        isStreaming: false,
        error: null,
      })
    }
    return conversations.value.get(researchId)!
  }

  const currentConversation = () => {
    if (!activeResearchId.value) return null
    return getConversation(activeResearchId.value)
  }

  // Actions
  function setActiveResearch(researchId: string) {
    activeResearchId.value = researchId
    if (!conversations.value.has(researchId)) {
      conversations.value.set(researchId, {
        messages: [],
        isConnected: false,
        isStreaming: false,
        error: null,
      })
    }
  }

  async function sendMessage(researchId: string, message: string): Promise<void> {
    const conversation = getConversation(researchId)

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }
    conversation.messages.push(userMessage)

    try {
      conversation.error = null

      // Get auth token
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('Not authenticated')
      }

      // Send message to API
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/chat/send`,
        {
          message,
          research_id: researchId,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.content,
        timestamp: response.data.timestamp,
        tool_uses: response.data.tool_uses,
      }
      conversation.messages.push(assistantMessage)
    } catch (err: any) {
      conversation.error = err.response?.data?.detail || 'Failed to send message'
      throw err
    }
  }

  function connectWebSocket(researchId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const conversation = getConversation(researchId)

      // Close existing connection
      if (websockets.value.has(researchId)) {
        const existingWs = websockets.value.get(researchId)!
        existingWs.close()
      }

      // Get auth token
      const token = localStorage.getItem('token')
      if (!token) {
        reject(new Error('Not authenticated'))
        return
      }

      // Create WebSocket connection
      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/v1/chat/ws/${researchId}`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        conversation.isConnected = true
        conversation.error = null
        websockets.value.set(researchId, ws)
        resolve()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'chunk') {
            // Streaming chunk
            if (conversation.isStreaming) {
              // Append to last message
              const lastMsg = conversation.messages[conversation.messages.length - 1]
              if (lastMsg && lastMsg.role === 'assistant') {
                lastMsg.content += data.content
              } else {
                // Start new streaming message
                conversation.messages.push({
                  role: 'assistant',
                  content: data.content,
                  timestamp: new Date().toISOString(),
                })
              }
            } else {
              // First chunk, start streaming
              conversation.isStreaming = true
              conversation.messages.push({
                role: 'assistant',
                content: data.content,
                timestamp: new Date().toISOString(),
              })
            }
          } else if (data.type === 'complete') {
            // Stream complete
            conversation.isStreaming = false
          } else if (data.type === 'error') {
            // Error
            conversation.error = data.content
            conversation.isStreaming = false
          } else if (data.type === 'tool_use') {
            // Tool usage notification
            const lastMsg = conversation.messages[conversation.messages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              if (!lastMsg.tool_uses) {
                lastMsg.tool_uses = []
              }
              lastMsg.tool_uses.push({
                tool: data.tool,
                arguments: data.arguments,
              })
            }
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        conversation.error = 'WebSocket connection error'
        conversation.isConnected = false
        reject(error)
      }

      ws.onclose = () => {
        conversation.isConnected = false
        conversation.isStreaming = false
        websockets.value.delete(researchId)
      }
    })
  }

  function sendWebSocketMessage(researchId: string, message: string) {
    const conversation = getConversation(researchId)
    const ws = websockets.value.get(researchId)

    if (!ws || ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }

    // Add user message to conversation
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }
    conversation.messages.push(userMessage)

    // Send via WebSocket
    ws.send(
      JSON.stringify({
        message,
        history: conversation.messages.slice(0, -1), // Don't include the message we just added
      })
    )
  }

  function disconnectWebSocket(researchId: string) {
    const ws = websockets.value.get(researchId)
    if (ws) {
      ws.close()
      websockets.value.delete(researchId)
    }

    const conversation = getConversation(researchId)
    conversation.isConnected = false
    conversation.isStreaming = false
  }

  function clearConversation(researchId: string) {
    const conversation = getConversation(researchId)
    conversation.messages = []
    conversation.error = null
  }

  function clearAllConversations() {
    // Close all websockets
    websockets.value.forEach((ws) => ws.close())
    websockets.value.clear()

    // Clear conversations
    conversations.value.clear()
    activeResearchId.value = null
  }

  return {
    // State
    conversations,
    activeResearchId,

    // Getters
    getConversation,
    currentConversation,

    // Actions
    setActiveResearch,
    sendMessage,
    connectWebSocket,
    sendWebSocketMessage,
    disconnectWebSocket,
    clearConversation,
    clearAllConversations,
  }
})
