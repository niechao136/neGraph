<template>
  <div class="chat-wrapper">
    <!-- 消息列表 -->
    <div class="chat-messages" ref="chatMessages">
      <div v-if="messages.length === 0" class="empty-placeholder">
        开始一段新的对话吧 👋
      </div>
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', index % 2 === 0 ? 'bot' : 'user']"
      >
        {{ msg }}
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-container">
      <chat-input @send="handleSend"/>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Ref } from 'vue-property-decorator'
import ChatInput from '@/components/ChatInput.vue'

@Component({
  components: { ChatInput }
})
export default class ChatDetail extends Vue {

  protected messages: string[] = []

  @Ref('chatMessages') readonly chatMessages!: HTMLDivElement

  handleSend(payload: { type: string, content: any }) {
    if (payload.type === 'text') {
      this.messages.push(payload.content)
      this.$nextTick(() => {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight
      })
    }
  }
}
</script>

<style scoped lang="scss">
.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #202123; /* 深灰背景 */
  color: #e5e5e5;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-placeholder {
  text-align: center;
  margin-top: 20%;
  color: #777;
  font-size: 16px;
}

.message {
  padding: 10px 14px;
  border-radius: 12px;
  max-width: 65%;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.message.bot {
  align-self: flex-start;
  background: #2b2c2f;
  color: #e5e5e5;
}

.message.user {
  align-self: flex-end;
  background: #3a7afe;
  color: #fff;
}

.input-container {
  padding: 12px 16px;
  border-top: 1px solid #333;
  background: #202123;
}
</style>
