<script lang="ts">
import {Component, Prop, Vue} from 'vue-property-decorator'
import { get } from '@/api'
import { LoginStore } from '@/stores/login'
import { getInitials } from '@/utils/string'


const loginStore = new LoginStore()

@Component({})
export default class ChatSidebar extends Vue {
  @Prop({ type: String, default: () => null })
  private activeId: string

  @Prop({ type: Number, default: () => 20 })
  private limit: number

  private collapsed = false
  private items: Chat.Info[] = []
  private has_more = true
  private loading = false
  private before: string | null = null
  private skeletonCount = 6

  private showUserMenu = false

  protected get user() {
    const username = loginStore.user?.username ?? ''
    const avatar = getInitials(username)
    return {
      avatar,
      username,
    }
  }

  /** 折叠/展开 */
  public toggleCollapse() {
    this.collapsed = !this.collapsed
  }

  private async loadMore() {
    if (this.loading || !this.has_more) return
    this.loading = true
    const data = {
      limit: this.limit,
      before: this.before,
    }
    const res = await get({ url: 'chat/list', data })
    const list: Chat.List = res?.data ?? {}
    if (Array.isArray(list?.data)) {
      this.has_more = !!list?.has_more
      const data = list?.data ?? []
      this.before = data[data.length - 1]?.created_at ?? null
      this.items = this.items.concat(data)
    }
    this.loading = false
  }

  private onScroll(e: Event) {
    const el = e.target as HTMLElement
    const threshold = 120 // 提前量，避免触底抖动
    if (el.scrollTop + el.clientHeight + threshold >= el.scrollHeight) {
      this.loadMore()
    }
  }

  private toggleUserMenu() {
    this.showUserMenu = !this.showUserMenu
  }

  private logout() {
    this.showUserMenu = false
    this.$emit('logout')
  }

  /** 点击空白处关闭菜单 */
  private handleClickOutside(e: MouseEvent) {
    const target = e.target as HTMLElement
    if (!this.$el.querySelector('.sidebar-footer')?.contains(target)) {
      this.showUserMenu = false
    }
  }

  protected async created() {
    this.items = []
    await this.loadMore()
  }

  protected async mounted() {
    document.addEventListener('click', this.handleClickOutside, true)
  }

  protected async beforeDestroy() {
    document.removeEventListener('click', this.handleClickOutside, true)
  }
}
</script>

<template>
  <aside :class="['chat-sidebar', { collapsed }]">
    <!-- Header -->
    <div class="sidebar-header">
      <button
        :title="collapsed ? '展开' : '折叠'"
        class="icon-btn"
        @click="toggleCollapse"
      >
        <svg
          height="24"
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          viewBox="0 0 24 24"
          width="24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect fill="none" height="18" rx="2" width="18" x="3" y="3"></rect>
          <path d="M15 3v18" fill="none"></path>
          <path
            :d="collapsed ? 'm8 9 3 3-3 3' : 'm10 15-3-3 3-3'"
            fill="none"
          ></path>
        </svg>
      </button>
      <a v-if="!collapsed" class="logo" href="/">GraphChat</a>
    </div>

    <!-- Body -->
    <div class="sidebar-body">
      <!-- Nav -->
      <nav class="menu">
        <div class="menu-item" @click="$emit('new-chat')">
          <span class="icon">＋</span>
          <span v-if="!collapsed">新聊天</span>
        </div>
      </nav>

      <!-- Record List -->
      <div v-if="!collapsed" ref="scrollWrap" class="record-list" @scroll="onScroll">
        <div class="record-title">聊天记录</div>
        <template v-if="items.length">
          <div
            v-for="item in items"
            :key="item.conversation_id"
            :class="['chat-item', { active: item.conversation_id === activeId }]"
            :title="item.summary"
            @click="$emit('select-chat', item)"
          >
            <div class="chat-title">{{ item.summary }}</div>
          </div>
        </template>
        <!-- Empty state -->
        <div v-if="!loading && !items.length" class="empty">暂无会话</div>
        <!-- Skeleton loader -->
        <div v-if="loading" class="skeleton-wrap">
          <div v-for="n in skeletonCount" :key="n" class="skeleton-item">
            <div class="skeleton-line shimmer"></div>
          </div>
        </div>
        <!-- Tail status -->
        <div v-if="!has_more && items.length && !loading" class="end-tip">已加载全部</div>
      </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer" @click="toggleUserMenu">
      <div class="user-avatar">{{ user.avatar }}</div>
      <div v-if="!collapsed" class="user-meta">
        <div class="username">{{ user.username }}</div>
      </div>
      <transition name="fade">
        <div v-if="showUserMenu" class="user-menu">
          <div class="menu-item" @click.stop="logout">注销</div>
        </div>
      </transition>
    </div>
  </aside>
</template>

<style lang="scss" scoped>
.chat-sidebar {
  height: 100vh;
  width: 288px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #1a1a1a;
  color: #f5f5f5;
  transition: width 0.3s ease;

  &.collapsed {
    width: 56px;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    padding: 8px;
    gap: 8px;

    .icon-btn {
      width: 32px;
      height: 32px;
      border: none;
      background-color: transparent;
      color: #aaa;
      cursor: pointer;
      &:hover {
        color: #fff;
      }
    }

    .logo {
      flex: 1;
      font-family: "Futura", serif;
      font-weight: bold;
      font-size: 18px;
      color: #fff;
      text-decoration: none;
      text-align: left;
    }
  }

  .sidebar-body {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 8px;
  }

  .menu {
    padding: 0 8px;
    .menu-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px;
      cursor: pointer;
      border-radius: 6px;
      color: #ddd;
      &:hover {
        background: #2a2a2a;
      }
      .icon {
        font-size: 18px;
      }
    }
  }

  .record-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 8px;

    .record-title {
      margin: 8px 0;
      font-size: 14px;
      color: #aaa;
      text-align: left;
      padding: 0 8px;
    }

    .chat-item {
      padding: 6px 8px;
      margin-bottom: 4px;
      border-radius: 6px;
      cursor: pointer;
      color: #ccc;
      &:hover {
        background: #2a2a2a;
        color: #fff;
      }
      &.active {
        background: #3a3a3a;
        color: #fff;
      }
    }

    .empty {
      text-align: left;
      margin-top: 20px;
      color: #777;
      padding: 0 8px;
    }

    .end-tip {
      text-align: left;
      margin: 10px 0;
      font-size: 12px;
      color: #555;
      padding: 0 8px;
    }

    .skeleton-wrap {
      .skeleton-item {
        height: 16px;
        background: #2a2a2a;
        margin: 6px 0;
        border-radius: 4px;
      }
    }
  }

  .sidebar-footer {
    position: relative;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: #111;
    cursor: pointer;

    .user-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #444;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: bold;
      color: #fff;
    }

    .user-meta {
      .username {
        font-size: 14px;
        font-weight: 500;
      }
      .plan {
        font-size: 12px;
        color: #999;
      }
    }

    .user-menu {
      position: absolute;
      bottom: 48px;
      left: 8px;
      background: #2a2a2a;
      border-radius: 6px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
      z-index: 9999;
      .menu-item {
        padding: 8px 12px;
        font-size: 14px;
        cursor: pointer;
        color: #eee;
        white-space: nowrap;
        &:hover {
          background: #3a3a3a;
        }
      }
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
