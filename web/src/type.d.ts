
declare namespace User {
  type Info = {
    user_id?: string
    username?: string
  }
}

declare namespace Chat {
  type List = {
    limit?: number
    has_more?: boolean
    data?: Info[]
  }
  type Info = {
    conversation_id?: string
    summary?: string
    created_at?: string
  }
}
