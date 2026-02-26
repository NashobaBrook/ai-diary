const API_BASE = '/api'

export async function setConfig(userId, config) {
  const res = await fetch(`${API_BASE}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, ...config })
  })
  return res.json()
}

export async function getConfig(userId) {
  const res = await fetch(`${API_BASE}/config/${userId}`)
  return res.json()
}

export async function chat(userId, message, date = null, signal = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message, date }),
    signal
  })
  return res.json()
}

export async function listDiaries(userId) {
  const res = await fetch(`${API_BASE}/diaries?user_id=${userId}`)
  return res.json()
}

export async function getDiaries(userId) {
  const res = await fetch(`${API_BASE}/diaries?user_id=${userId}`)
  return res.json()
}

export async function getDiary(userId, date) {
  const res = await fetch(`${API_BASE}/diary/${date}?user_id=${userId}`)
  return res.json()
}

export async function getCalendar(userId, year, month) {
  const res = await fetch(`${API_BASE}/calendar/${year}/${month}?user_id=${userId}`)
  return res.json()
}

export async function getStats(userId) {
  const res = await fetch(`${API_BASE}/stats?user_id=${userId}`)
  return res.json()
}

export async function setFeishuConfig(config) {
  const res = await fetch(`${API_BASE}/feishu/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  })
  return res.json()
}

export async function getFeishuConfig() {
  const res = await fetch(`${API_BASE}/feishu/config`)
  return res.json()
}

export async function getConversation(userId, date = null) {
  const d = date || new Date().toISOString().split('T')[0]
  const res = await fetch(`${API_BASE}/conversation/${d}?user_id=${userId}`)
  return res.json()
}

export async function generateDiary(userId, date = null) {
  const url = date 
    ? `${API_BASE}/diary/generate?user_id=${userId}&target_date=${date}`
    : `${API_BASE}/diary/generate?user_id=${userId}`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  return res.json()
}

export async function checkPendingDiary(userId) {
  const res = await fetch(`${API_BASE}/diary/pending?user_id=${userId}`)
  return res.json()
}

export async function analyzeWritingStyle(userId) {
  const res = await fetch(`${API_BASE}/user/analyze-style?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  return res.json()
}

export async function getUserStyle(userId) {
  const res = await fetch(`${API_BASE}/user/style/${userId}`)
  return res.json()
}

export async function saveUserStyle(userId, content) {
  const res = await fetch(`${API_BASE}/user/style/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })
  return res.json()
}

export async function updateDiary(userId, date, data) {
  const res = await fetch(`${API_BASE}/diary/${date}?user_id=${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export async function regenerateDiary(userId, date) {
  const res = await fetch(`${API_BASE}/diary/${date}/regenerate?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  return res.json()
}
