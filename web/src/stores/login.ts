import { Store, Pinia } from 'pinia-class-component'
import { post } from '@/api'
import { COOKIE_KEY, CRYPTO_KEY } from '@/config'
import { getCookie, rmCookie, setCookie } from '@/utils/cookie'
import { aesDecrypt, aesEncrypt } from '@/utils/crypto'


@Store
export class LoginStore extends Pinia {
  _token = ''
  initToken() {
    let _token = ''
    const token = getCookie(COOKIE_KEY.TOKEN)
    if (!!token) {
      _token = aesDecrypt(token, CRYPTO_KEY.TOKEN)
    }
    this._token = _token
  }

  async login(username: string, password: string) {
    const data = {
      password,
      username
    }
    const res = await post({ url: 'auth/login', data })
    if (res?.data?.status === 1) {
      this._token = res?.data?.access_token ?? ''
      setCookie(COOKIE_KEY.TOKEN, aesEncrypt(this._token, CRYPTO_KEY.TOKEN), null)
    }
    return res?.data
  }

  logout() {
    rmCookie(COOKIE_KEY.TOKEN)
    this._token = ''
  }

  async register(username: string, password: string, email: string) {
    const data = {
      email,
      password,
      username
    }
    const res = await post({ url: 'auth/register', data })
    if (res?.data?.status === 1) {
      this._token = res?.data?.access_token ?? ''
      setCookie(COOKIE_KEY.TOKEN, aesEncrypt(this._token, CRYPTO_KEY.TOKEN), null)
    }
    return res?.data
  }

}
