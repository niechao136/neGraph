import Vue from 'vue'
import { createPinia, PiniaVuePlugin } from 'pinia'
import VueCompositionAPI from '@vue/composition-api'
import App from './App.vue'
import router from './router'
import './assets/scss/index.scss'

Vue.config.productionTip = false


const pinia = createPinia()
Vue.use(VueCompositionAPI)
Vue.use(PiniaVuePlugin)

new Vue({
  router,
  pinia,
  render: h => h(App)
}).$mount('#app')
