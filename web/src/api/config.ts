import axios, { AxiosRequestConfig } from 'axios'
import { LoginStore } from '@/stores/login'

const config: AxiosRequestConfig = {
  timeout: 300 * 1000, // Timeout
  baseURL: 'http://150.109.15.178:10086/',
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
}

const service = axios.create(config)

const NOT_NEED_TOKEN: string[] = [
  'auth/login',
  'auth/register'
]

service.interceptors.request.use(
  config => {
    if (!NOT_NEED_TOKEN.find(o => config?.url?.endsWith(o))) {
      const login = new LoginStore()
      config.headers.Authorization = `Bearer ${login._token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

export default service

