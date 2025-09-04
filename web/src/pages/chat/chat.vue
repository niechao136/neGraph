<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import ChatSidebar from './ChatSidebar.vue'

@Component({
  components: {
    ChatSidebar
  }
})
export default class chat extends Vue {

}
</script>

<template>
  <div class="chat">
    <chat-sidebar/>
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
