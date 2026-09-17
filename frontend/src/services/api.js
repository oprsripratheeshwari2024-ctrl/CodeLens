import axios from 'axios'

const BASE_URL = 'http://localhost:8000/api'
const client = axios.create({ baseURL: BASE_URL })

export const api = {
  login: (email) => client.post('/login', { email }).then(r => r.data),

  dashboard: (userId) => client.get(`/dashboard/${userId}`).then(r => r.data),

  analyze: (userId, language, code, mode) =>
    client.post('/analyze', { user_id: userId, language, code, mode }).then(r => r.data),

  history: (userId) => client.get('/history', { params: { user_id: userId } }).then(r => r.data),

  historyDetail: (userId, analysisId) =>
    client.get(`/history/${analysisId}`, { params: { user_id: userId } }).then(r => r.data),

  reportUrl: (userId, analysisId) =>
    `${BASE_URL}/report/${analysisId}?user_id=${userId}`,

  submitReview: (userId, rating, feedback) =>
    client.post('/review', { user_id: userId, rating, feedback }).then(r => r.data),

  flowStepExplain: (label, codeLine, language) =>
    client.post('/flow-step-explain', { label, code_line: codeLine, language }).then(r => r.data),

  explainLines: (userId, language, code, mode) =>
    client.post('/explain-lines', { user_id: userId, language, code, mode }).then(r => r.data),
}

export default api
