<template>
  <div class="chat-input">
    <textarea
      v-model="message"
      ref="textarea"
      placeholder="输入消息..."
      @input="autoResize"
      @keyup.enter.exact.prevent="sendMessage"
      class="chat-textarea"
    ></textarea>

    <!-- 工具栏 -->
    <div class="chat-tools">
      <!-- 文件上传 -->
      <label class="icon-btn upload-btn">
        📎
        <input type="file" @change="handleFileUpload" hidden />
      </label>

      <!-- 语音（点击开始/停止） -->
      <button class="icon-btn voice-btn" @click="toggleRecording">
        🎤
        <div v-if="recording" class="voice-ripple">
          <span v-for="n in 3" :key="n" class="circle"></span>
        </div>
      </button>

      <!-- 发送 -->
      <button class="send-btn" @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Ref } from 'vue-property-decorator'

@Component({})
export default class ChatInput extends Vue {
  message: string = ''
  recording: boolean = false
  mediaRecorder: MediaRecorder | null = null
  audioChunks: BlobPart[] = []

  @Ref('textarea') readonly textarea!: HTMLTextAreaElement
  @Ref('fileInput') readonly fileInput!: HTMLInputElement

  sendMessage() {
    if (this.message.trim() !== '') {
      this.$emit('send', { type: 'text', content: this.message })
      this.message = ''
      this.autoResize()
    }
  }

  handleFileUpload(event: Event) {
    const files = (event.target as HTMLInputElement).files
    if (files && files.length > 0) {
      this.$emit('send', { type: 'file', content: files[0] })
      ;(event.target as HTMLInputElement).value = ''
    }
  }

  autoResize() {
    const el = this.textarea
    el.style.height = 'auto'
    // 恢复最小高度
    if (this.message.trim() === "") {
      el.style.height = "40px";
    } else {
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }

  async toggleRecording() {
    if (this.recording) {
      // 停止录音
      this.mediaRecorder?.stop()
      this.recording = false
    } else {
      // 开始录音
      if (!navigator.mediaDevices) return
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      this.mediaRecorder = new MediaRecorder(stream)
      this.audioChunks = []

      this.mediaRecorder.ondataavailable = (e) => {
        this.audioChunks.push(e.data)
      }
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
        this.$emit('send', { type: 'audio', content: audioBlob })
        this.audioChunks = []
      }

      this.mediaRecorder.start()
      this.recording = true
    }
  }
}
</script>

<style scoped lang="scss">
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 10px;
  border: 1px solid #444;
  border-radius: 12px;
  background: #2b2c2f;
}

.chat-textarea {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  border: none;
  resize: none;
  line-height: 1.5;
  font-size: 14px;
  background: transparent;
  color: #e5e5e5;
  max-height: 200px;
  overflow-y: auto;
}
.chat-textarea:focus {
  outline: none;
}
/* 去掉原始滚动条并自定义暗色滚动条样式 */
.chat-textarea::-webkit-scrollbar {
  width: 6px;
}
.chat-textarea::-webkit-scrollbar-track {
  background: transparent; /* 滚动条轨道透明 */
}
.chat-textarea::-webkit-scrollbar-thumb {
  background: #555;  /* 深灰 */
  border-radius: 3px;
}
.chat-textarea::-webkit-scrollbar-thumb:hover {
  background: #777; /* hover 时稍亮 */
}

.chat-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn {
  cursor: pointer;
  font-size: 18px;
  color: #aaa;
  box-sizing: border-box;
}

.voice-btn {
  position: relative;
  cursor: pointer;
  font-size: 18px;
  color: #aaa;
  background: transparent;
  border: none;
}

.voice-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 1;
}
.voice-ripple .circle {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(76, 175, 239, 0.4);
  animation: ripple 1.5s infinite;
}
.voice-ripple .circle:nth-child(2) {
  animation-delay: 0.5s;
}
.voice-ripple .circle:nth-child(3) {
  animation-delay: 1s;
}
@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}

.icon-btn {
  width: 36px;
  height: 36px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 6px;
  border-radius: 36px;
  color: #e5e5e5;
  transition: background 0.2s;
}
.icon-btn:hover {
  background: #3a3a3a;
}

.send-btn {
  background: #3a7afe;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 14px;
}
.send-btn:hover {
  background: #5a8bff;
}
</style>
