<script lang="ts">
import {Vue, Component} from 'vue-property-decorator';
import { LoginStore } from '@/stores/login'


const loginStore = new LoginStore()
@Component({})
export default class login extends Vue {
  isLogin: boolean = true;
  username: string = "";
  email: string = ""
  password: string = "";
  confirmPassword: string = "";

  toggleMode() {
    this.isLogin = !this.isLogin;
    this.username = "";
    this.email = "";
    this.password = "";
    this.confirmPassword = "";
  }

  async handleSubmit() {
    if (!this.username || !this.password) return;

    if (!this.isLogin && this.password !== this.confirmPassword) {
      alert("两次输入的密码不一致");
      return;
    }

    if (this.isLogin) {
      const res = await loginStore.login(this.username, this.password)
      if (res?.status === 1) {
        await this.$router.push("/new");
      } else {
         alert(res?.error_msg ?? '登入失败');
      }
    } else {
      const res = await loginStore.register(this.username, this.password, this.email)
      if (res?.status === 1) {
        await this.$router.push("/new");
      } else {
         alert(res?.error_msg ?? '注册失败');
      }
    }
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>{{ isLogin ? "登录" : "注册" }}</h2>

      <form @submit.prevent="handleSubmit">
        <div class="form-item">
          <label for="username">用户名</label>
          <input id="username" v-model="username" placeholder="请输入用户名" required type="text"/>
        </div>

        <div v-if="!isLogin" class="form-item">
          <label for="email">Email</label>
          <input id="email" v-model="email" placeholder="请输入 Email" type="text"/>
        </div>

        <div class="form-item">
          <label for="password">密码</label>
          <input id="password" v-model="password" placeholder="请输入密码" required type="password"/>
        </div>

        <div v-if="!isLogin" class="form-item">
          <label for="confirm">确认密码</label>
          <input id="confirm" v-model="confirmPassword" placeholder="请再次输入密码" required type="password"/>
        </div>

        <button class="submit-btn" type="submit">
          {{ isLogin ? "登录" : "注册" }}
        </button>
      </form>

      <div class="switch-mode">
        <span>{{ isLogin ? "还没有账号？" : "已有账号？" }}</span>
        <a href="javascript:void(0)" @click="toggleMode">
          {{ isLogin ? "去注册" : "去登录" }}
        </a>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #f5f7fa;
}

.auth-card {
  width: 400px;
  padding: 24px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  text-align: center;

  h2 {
    margin-bottom: 20px;
    font-weight: bold;
    font-size: 20px;
    color: #2c3e50;
  }

  .form-item {
    text-align: left;
    margin-bottom: 16px;

    label {
      display: block;
      margin-bottom: 4px;
      font-size: 14px;
      color: #555;
    }

    input {
      width: 378px;
      padding: 8px 10px;
      border-radius: 6px;
      border: 1px solid #ccc;
      font-size: 14px;

      &:focus {
        outline: none;
        border-color: #409eff;
      }
    }
  }

  .submit-btn {
    width: 100%;
    padding: 10px;
    margin-top: 8px;
    border: none;
    border-radius: 6px;
    background: #409eff;
    color: #fff;
    font-size: 16px;
    cursor: pointer;

    &:hover {
      background: #66b1ff;
    }
  }

  .switch-mode {
    margin-top: 12px;
    font-size: 14px;
    color: #666;

    a {
      color: #409eff;
      margin-left: 4px;
      cursor: pointer;
    }
  }
}
</style>
