import Cookie from 'js-cookie'

export const getCookie = (key: string) => Cookie.get(key)

export const rmCookie = (key: string) => Cookie.remove(key)

export const setCookie = (key: string, value: string, expires: number | null = 1) => {
  if (!!expires) {
    Cookie.set(key, value, { expires })
  } else {
    Cookie.set(key, value)
  }
}
