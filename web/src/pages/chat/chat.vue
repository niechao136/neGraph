<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import { get } from '@/api'
import { LoginStore } from '@/stores/login'
import ChatSidebar from './ChatSidebar.vue'


const loginStore = new LoginStore()
@Component({
  components: {
    ChatSidebar
  }
})
export default class chat extends Vue {
  protected async logout() {
    loginStore.logout()
    await this.$router.push('/login')
  }

  protected async created() {
    await loginStore.getUser()
  }
}
</script>

<template>
  <div class="chat">
    <chat-sidebar
      @logout="logout"
    />
    <div class="chat-body">
      <router-view/>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat {
  display: flex;
  .chat-body {
    flex: 1;
    background-color: #262624;
  }
}
</style>
