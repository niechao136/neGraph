import Vue from 'vue'
import VueRouter, { RouteConfig } from 'vue-router'
import { LoginStore } from '@/stores/login'

Vue.use(VueRouter)

const routes: Array<RouteConfig> = [
  {
    path: '/',
    name: 'chat',
    component: () => import(/* webpackChunkName: "chat" */ '@/pages/chat/chat.vue'),
    children: [
      {
        path: 'new',
        name: 'new',
        component: () => import(/* webpackChunkName: "chat_detail" */ '@/pages/chat/ChatDetail.vue')
      },
      {
        path: 'chat/:id',
        component: () => import(/* webpackChunkName: "chat_detail" */ '@/pages/chat/ChatDetail.vue')
      },
      {
        path: '',
        redirect: { name: 'new' }
      }
    ]
  },
  {
    path: '/login',
    component: () => import(/* webpackChunkName: "login" */ '@/pages/auth/login.vue'),
  },
  {
    path: '*',
    redirect: { name: 'chat' }
  }
]

const router = new VueRouter({
  mode: 'history',
  routes
})

const NOT_NEED_LOGIN = [
  '/login',
]

router.afterEach(async (to) => {
  if (!NOT_NEED_LOGIN.find(s => to.path.startsWith(s))) {
    const login = new LoginStore()
    if (!login._token) {
      login.initToken()
      if (!login._token) {
        await router.push('/login')
      }
    }
  }
})

export default router
