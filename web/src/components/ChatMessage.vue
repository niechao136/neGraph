<script lang="ts">
import { Vue, Component, Prop } from "vue-property-decorator";
import { marked } from "marked";
import DOMPurify from "dompurify";
import highlight from "highlight.js";
import "highlight.js/styles/github-dark.css";


const renderer = new marked.Renderer();
renderer.link = ({ href, title, text }) => {
  return `<a href="${href}" target="_blank" rel="noopener" title="${title}">${text}</a>`;
};
renderer.code = ({ text, lang }) => {
  const encodedCode = encodeURIComponent(text);
  const validLang = lang && highlight.getLanguage(lang) ? lang : "plaintext";
  const highlighted = highlight.highlight(text, { language: validLang }).value;
  return `
    <div class="code-card">
      <div class="code-header">
        <span class="lang">${validLang || ""}</span>
        <button class="copy-btn" data-code="${encodedCode}">📋</button>
      </div>
      <pre><code class="hljs language-${validLang || ""}">${highlighted}</code></pre>
    </div>
  `;
};
marked.setOptions({ renderer });
const config = {
  ADD_ATTR: ["target"], // 允许 target 属性
  ADD_URI_SAFE_ATTR: ["target"], // 标记 target 为安全属性
  // 自动添加 rel="noopener noreferrer"
  AFTER_SANITIZE_ATTRIBUTES: (node: HTMLElement, { attrName, attrValue }: { attrName: string; attrValue: string }) => {
    if (attrName === "target" && attrValue === "_blank") {
      node.setAttribute("rel", "noopener noreferrer");
    }
    return node;
  },
};
@Component({})
export default class ChatMessage extends Vue {
  @Prop({
    type: Object,
    default: () => Object({}),
  })
  private message: Chat.Message;

  private init_option = []

  private get init_text() {
    return "Hi! How can I help you today?";
  }

  private clickOption(option: string) {
    this.$emit("clickOption", option);
  }

  private marked(text?: string) {
    const no_think = String(text ?? "")
      .replaceAll(/<think>[\s\S]*?<\/think>/g, "")
      .replaceAll(/<details[\s\S]*?<\/details>/g, "");
    const rawHtml = marked.parse(no_think) as string;
    return DOMPurify.sanitize(rawHtml, config);
  }

  private getTime(dateStr: string) {
    const date = new Date(dateStr);
    const now = new Date();

    // helper: 判断是否同一天
    const isSameDay = (d1: Date, d2: Date) =>
      d1.getFullYear() === d2.getFullYear() && d1.getMonth() === d2.getMonth() && d1.getDate() === d2.getDate();

    // helper: 判断是否昨天
    const isYesterday = (d: Date, now: Date) => {
      const yesterday = new Date(now);
      yesterday.setDate(now.getDate() - 1);
      return isSameDay(d, yesterday);
    };

    const period = now.getTime() - date.getTime(); // 毫秒差

    const oneDay = 24 * 60 * 60 * 1000;
    const oneWeek = 7 * oneDay;

    if (isSameDay(date, now)) return "Today";
    if (isYesterday(date, now)) return "Yesterday";

    if (period < oneWeek) {
      return Math.floor(period / oneDay) + " days ago";
    }

    const oneMonthMs = 30 * oneDay;
    if (period < 12 * oneMonthMs) {
      // 计算月份
      let month = 1;
      while (period >= month * oneMonthMs) {
        month++;
      }
      return month + " months ago";
    }

    // 年份
    let year = 1;
    const oneYearMs = 365 * oneDay;
    while (period >= year * oneYearMs) {
      year++;
    }
    return year + " years ago";
  }

  protected async mounted() {
    this.$nextTick(() => {
      document.querySelectorAll(".copy-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const code = decodeURIComponent((btn as HTMLElement).getAttribute("data-code") || "");
          if (navigator.clipboard && navigator.clipboard.writeText) {
            try {
              navigator.clipboard.writeText(code);
              return true;
            } catch (err) {
              console.warn("Clipboard API 复制失败，尝试 fallback", err);
            }
          }
          // fallback：使用 document.execCommand
          try {
            const textarea = document.createElement("textarea");
            textarea.value = code;
            // 防止滚动条闪烁
            textarea.style.position = "fixed";
            textarea.style.top = "-9999px";
            document.body.appendChild(textarea);
            textarea.select();
            const success = document.execCommand("copy");
            document.body.removeChild(textarea);
            return success;
          } catch (err) {
            console.error("execCommand 复制失败", err);
            return false;
          }
        });
      });
    });
  }
}
</script>

<template>
  <div :class="['chat-message', message.type]">
    <div v-if="message.type === 'init'" class="message-time">
      <div class="message-time__text">{{ getTime(message.timestamp) }}</div>
    </div>
    <div class="message-content">
      <div v-if="message.type !== 'question'" class="message-avatar"></div>
      <div v-if="message.type === 'init'" class="message-init">
        <div class="message-text">{{ init_text }}</div>
        <div v-for="(option, key) in init_option" class="message-option" :key="key" @click="clickOption(option)">
          {{ option }}
        </div>
      </div>
      <div v-if="message.type === 'question'" class="message-question">
        <div v-if="message.loading" class="loading">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div v-else class="question-text">{{ message.content }}</div>
      </div>
      <div v-if="message.type === 'answer'" class="message-answer">
        <div class="answer-content">
          <div v-if="message.loading" class="loading">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div v-else class="answer-text" v-html="marked(message.content)"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-message {
  display: flex;
  flex-direction: column;
  padding: 8px 16px;
  gap: 16px;

  .message-time {
    display: flex;
    justify-content: center;
    .message-time__text {
      padding: 4px 10px;
      border-radius: 12px;
      background: #2c2c2c;
      color: #aaa;
      text-align: center;
      font-size: 12px;
      line-height: 16px;
      font-weight: 400;
    }
  }

  .message-content {
    display: flex;
    gap: 8px;

    .message-avatar {
      min-width: 40px;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-image: url("@/assets/images/avatar.png");
      background-size: cover;
      background-position: center;
    }

    .message-init {
      display: flex;
      flex-direction: column;
      padding: 8px 0;
      gap: 8px;

      .message-text {
        color: #e5e5e5;
        font-size: 14px;
        line-height: 20px;
      }

      .message-option {
        border-radius: 6px;
        border: 1px solid #555;
        padding: 10px;
        color: #4dabf7;
        text-align: left;
        font-size: 14px;
        font-weight: 600;
        line-height: 20px;
        cursor: pointer;
        background: #1e1e1e;
        transition: background 0.2s;

        &:hover {
          background: #2a2a2a;
        }
      }
    }

    .message-question {
      max-width: 70%;
      padding: 10px 14px;
      border-radius: 18px 18px 4px 18px;
      background: #3a7afe;
      align-self: flex-end;

      .question-text {
        color: #fff;
        font-size: 14px;
        line-height: 20px;
      }
    }

    .message-answer {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-width: 70%;
      padding: 10px 14px;
      border-radius: 18px 18px 18px 4px;
      background: #2a2a2a;
      align-self: flex-start;

      .answer-text {
        color: #e5e5e5;
        font-size: 14px;
        line-height: 20px;

        ::v-deep {
          * {
            margin: 0;
            word-break: break-word;
          }

          a {
            color: #4dabf7;
            text-decoration: underline;
          }

          .code-card {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 0.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          }

          .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.25rem 0.5rem;
            background: #2c2c2c;
            border-radius: 6px 6px 0 0;
            color: #bbb;
            font-size: 12px;
          }

          .copy-btn {
            background: transparent;
            border: none;
            color: #4dabf7;
            cursor: pointer;
            font-size: 12px;
            &:hover {
              opacity: 0.7;
            }
          }

          .code-card pre {
            margin: 0;
            padding: 0.5rem;
            overflow-x: auto;
            background: #1e1e1e;
          }

          code:not(.hljs) {
            background-color: #2c2c2c;
            color: #f08d49;
            padding: 2px 4px;
            border-radius: 4px;
            font-size: 0.95em;
          }
        }
      }
    }

    .loading {
      height: 24px;
      width: 40px;
      display: flex;
      justify-content: center;
      align-items: center;
      span {
        display: inline-block;
        width: 6px;
        height: 6px;
        margin: 0 2px;
        background-color: #aaa;
        border-radius: 50%;
        animation: loading 1.4s infinite ease-in-out both;

        &:nth-child(1) {
          animation-delay: -0.32s;
        }
        &:nth-child(2) {
          animation-delay: -0.16s;
        }
      }

      @keyframes loading {
        0%,
        80%,
        100% {
          transform: scale(0);
        }
        40% {
          transform: scale(1);
        }
      }
    }
  }

  &.question {
    padding: 8px 16px 8px 112px;

    .message-content {
      flex-direction: row-reverse;
    }
  }
}
</style>

