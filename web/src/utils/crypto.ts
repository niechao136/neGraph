import CryptoJS from 'crypto-js'

const getAesKey = (key: string) => {
  const Utf8Encode = new TextEncoder()
  const newArray = new Uint8Array(16)
  const keyArray = Utf8Encode.encode(key)
  for (let i = 0; i < newArray.length; i++) {
    newArray[i] = i >= keyArray.length ? 0 : keyArray[i]
  }
  return newArray
}

export const aesDecrypt = (encrypted: string, key: string) => {
  const aesKey = CryptoJS.lib.WordArray.create(getAesKey(key) as any)
  encrypted = encrypted.replace(' ', '')
  // 这里 mode, padding 一定要跟加密的时候完全一样
  // 返回的是一个解密后的对象
  const decrypt = CryptoJS.AES.decrypt(encrypted, aesKey, {
    mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.Pkcs7,
  })
  // 将解密对象转换成 UTF8 的字符串
  //console.log(decrypt, key)
  return CryptoJS.enc.Utf8.stringify(decrypt)
}

export const aesEncrypt = (encrypt: string, key: string) => {
  const aesKey = CryptoJS.lib.WordArray.create(getAesKey(key) as any)
  const encrypted = CryptoJS.AES.encrypt(encrypt, aesKey, {
    mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.Pkcs7,
  })
  return encrypted.toString()
}

export const md5Encrypt = (target: string) => {
  return CryptoJS.MD5(target).toString()
}
