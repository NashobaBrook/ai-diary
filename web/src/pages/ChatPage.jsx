import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chat, getConversation, generateDiary, getDiary, checkPendingDiary } from '../utils/api'
import Dialog from '../components/Dialog'
import { useDialog } from '../hooks/useDialog'

const MOOD_CONFIG = { 
  1: { icon: '😢', name: '沮丧' }, 
  2: { icon: '😕', name: '不高兴' }, 
  3: { icon: '🙂', name: '正常' }, 
  4: { icon: '😄', name: '有点喜悦' }, 
  5: { icon: '🥳', name: '超开心' } 
}

const BookIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '24px', height: '24px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
  </svg>
)

const CalendarIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '24px', height: '24px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18-0v-1.5m0 1.5v-1.5m0 0l1.5 1.5m-1.5-1.5l1.5-1.5" />
  </svg>
)

const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '24px', height: '24px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
  </svg>
)

const ChatIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '24px', height: '24px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.486.544.471 1.179.863 1.852 1.152 1.493.652 2.633 1.02 3.875 1.02 4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25z" />
  </svg>
)

const SparkleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '24px', height: '24px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
  </svg>
)

const CalendarDaysIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '24px', height: '24px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 2.25A.75.75 0 017.5 3v1.5h9V3A.75.75 0 0118 3v1.5h.75a3 3 0 013 3v11.25a3 3 0 01-3 3H5.25a3 3 0 01-3-3V7.5a3 3 0 013-3H6V3a.75.75 0 01.75-.75zm13.5 9a1.5 1.5 0 00-1.5-1.5H5.25a1.5 1.5 0 00-1.5 1.5v7.5a1.5 1.5 0 001.5 1.5h13.5a1.5 1.5 0 001.5-1.5v-7.5z" />
  </svg>
)

export default function ChatPage({ userId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [generatingDiary, setGeneratingDiary] = useState(false)
  const [todayDiary, setTodayDiary] = useState(null)
  const [showDiaryModal, setShowDiaryModal] = useState(false)
  const [pendingInput, setPendingInput] = useState('')
  const [hasPendingMessage, setHasPendingMessage] = useState(false)
  const [pendingDiaryInfo, setPendingDiaryInfo] = useState(null)
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [isToday, setIsToday] = useState(true)
  const abortControllerRef = useRef(null)
  const pendingInputRef = useRef('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const { dialog, showSuccess, showError, showConfirm } = useDialog()

  const getTodayString = () => new Date().toISOString().split('T')[0]

  useEffect(() => {
    loadTodayConversation()
    loadTodayDiary()
    checkPendingDiaryOnLoad()
  }, [userId])

  useEffect(() => {
    loadConversationForDate(selectedDate)
    loadDiaryForDate(selectedDate)
    setIsToday(selectedDate === getTodayString())
  }, [selectedDate])

  const loadTodayConversation = async () => {
    await loadConversationForDate(getTodayString())
  }

  const loadConversationForDate = async (date) => {
    try {
      const { messages: history } = await getConversation(userId, date)
      if (history && history.length > 0) {
        const formattedMessages = history.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
        setMessages(formattedMessages)
      } else {
        setMessages([])
      }
    } catch (e) {
      console.error('加载对话历史失败:', e)
      setMessages([])
    }
  }

  const loadTodayDiary = async () => {
    await loadDiaryForDate(getTodayString())
  }

  const loadDiaryForDate = async (date) => {
    try {
      const diary = await getDiary(userId, date)
      if (diary && !diary.code) {
        setTodayDiary(diary)
      } else {
        setTodayDiary(null)
      }
    } catch (e) {
      console.log('该日期暂无日记')
      setTodayDiary(null)
    }
  }

  const handleDateChange = (e) => {
    const newDate = e.target.value
    if (newDate > getTodayString()) {
      showError('不能选择未来的日期')
      return
    }
    setSelectedDate(newDate)
  }

  const checkPendingDiaryOnLoad = async () => {
    try {
      const result = await checkPendingDiary(userId)
      if (result.has_pending) {
        setPendingDiaryInfo(result)
        const confirmed = await showConfirm({
          title: '未生成日记',
          message: result.message,
          confirmText: '生成日记',
          cancelText: '稍后再说'
        })

        if (confirmed) {
          await handleGenerateDiaryForDate(result.date)
        }
      }
    } catch (e) {
      console.error('检查未生成日记失败:', e)
    }
  }

  const handleGenerateDiaryForDate = async (date) => {
    try {
      setGeneratingDiary(true)
      const result = await generateDiary(userId, date)
      showSuccess(result.message || '日记生成成功')
      setPendingDiaryInfo(null)
    } catch (e) {
      const message = e.response?.data?.message || '生成失败'
      showError(message)
    } finally {
      setGeneratingDiary(false)
    }
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setLoading(false)
  }

  const handleSend = async (appendContent = '') => {
    const contentToSend = appendContent || input.trim()
    if (!contentToSend || loading) return

    const userMsg = { role: 'user', content: contentToSend }
    setMessages(msgs => [...msgs, userMsg])
    setInput('')
    setPendingInput('')
    pendingInputRef.current = ''
    setHasPendingMessage(false)
    setLoading(true)

    abortControllerRef.current = new AbortController()

    try {
      const { reply, code, message } = await chat(userId, contentToSend, selectedDate, abortControllerRef.current.signal)
      if (code) {
        setMessages(msgs => [...msgs, { role: 'assistant', content: message || '发送失败' }])
      } else {
        setMessages(msgs => [...msgs, { role: 'assistant', content: reply }])
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        setMessages(msgs => [...msgs, { role: 'assistant', content: '（已停止回复）' }])
      } else {
        setMessages(msgs => [...msgs, { role: 'assistant', content: '连接失败，请检查配置' }])
      }
    }
    
    abortControllerRef.current = null
    setLoading(false)
    
    const nextContent = pendingInputRef.current.trim()
    if (nextContent) {
      pendingInputRef.current = ''
      setPendingInput('')
      setHasPendingMessage(false)
      setTimeout(() => {
        handleSend(nextContent)
      }, 100)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (loading) {
        if (input.trim()) {
          const newPending = pendingInputRef.current 
            ? pendingInputRef.current + '\n' + input.trim() 
            : input.trim()
          pendingInputRef.current = newPending
          setPendingInput(newPending)
          setHasPendingMessage(true)
          setInput('')
        }
      } else if (input.trim()) {
        handleSend()
      }
    }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
  }

  const handleGenerateDiary = async () => {
    if (generatingDiary || messages.length === 0) return

    setGeneratingDiary(true)
    try {
      const result = await generateDiary(userId, isToday ? null : selectedDate)
      if (result.diary) {
        setTodayDiary(result.diary)
        showSuccess(result.message || '日记生成成功')
        setShowDiaryModal(true)
      } else if (result.code) {
        showError(result.message || '生成失败')
      }
    } catch (e) {
      const message = e.response?.data?.message || '生成日记失败'
      showError(message)
    }
    setGeneratingDiary(false)
  }

  const handleViewDiary = () => {
    if (todayDiary) {
      setShowDiaryModal(true)
    }
  }

  const [inputFocused, setInputFocused] = useState(false)

  const styles = {
    wrapper: {
      display: 'flex',
      gap: '20px',
      height: 'calc(100vh - 112px)',
      margin: '0 auto'
    },
    sidebar: {
      width: '280px',
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: '12px'
    },
    sidebarCard: {
      background: '#fff',
      borderRadius: '12px',
      padding: '16px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      border: '1px solid #F3F4F6'
    },
    sidebarCardLarge: {
      background: '#fff',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      border: '1px solid #F3F4F6'
    },
    sidebarTitle: {
      fontSize: '13px',
      fontWeight: 600,
      color: '#374151',
      marginBottom: '10px',
      display: 'flex',
      alignItems: 'center',
      gap: '6px'
    },
    sidebarText: {
      fontSize: '13px',
      color: '#6B7280',
      lineHeight: 1.5
    },
    container: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      background: '#fff',
      borderRadius: '12px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      border: '1px solid #F3F4F6',
      overflow: 'hidden'
    },
    header: {
      padding: '16px 20px',
      borderBottom: '1px solid #F3F4F6',
      background: '#fff'
    },
    title: {
      fontSize: '16px',
      fontWeight: 600,
      color: '#1A1A1A',
      marginBottom: '2px'
    },
    subtitle: {
      fontSize: '13px',
      color: '#9CA3AF'
    },
    messages: {
      flex: 1,
      padding: '20px',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '14px',
      background: '#FAFAFA'
    },
    empty: {
      textAlign: 'center',
      color: '#9CA3AF',
      padding: '60px 0',
      fontSize: '14px'
    },
    bubble: {
      maxWidth: '80%',
      padding: '12px 16px',
      borderRadius: '12px',
      fontSize: '14px',
      lineHeight: 1.6,
      wordBreak: 'break-word'
    },
    userBubble: {
      alignSelf: 'flex-end',
      background: '#611208',
      color: '#fff',
      borderBottomRightRadius: '4px'
    },
    aiBubble: {
      alignSelf: 'flex-start',
      background: '#fff',
      color: '#1A1A1A',
      border: '1px solid #F3F4F6',
      borderBottomLeftRadius: '4px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
    },
    loading: {
      alignSelf: 'flex-start',
      background: '#fff',
      color: '#9CA3AF',
      border: '1px solid #F3F4F6',
      padding: '12px 16px',
      borderRadius: '12px',
      borderBottomLeftRadius: '4px'
    },
    inputArea: {
      padding: '16px 20px',
      background: '#fff',
      borderTop: '1px solid #F3F4F6',
      display: 'flex',
      gap: '10px',
      alignItems: 'flex-end'
    },
    input: {
      flex: 1,
      padding: '12px 16px',
      border: inputFocused ? '2px solid #611208' : '1px solid #E5E7EB',
      borderRadius: '12px',
      fontSize: '14px',
      outline: 'none',
      transition: 'all 150ms ease',
      background: '#FAFAFA',
      resize: 'none',
      minHeight: '48px',
      maxHeight: '120px',
      fontFamily: 'inherit'
    },
    button: (disabled) => ({
      padding: '12px 24px',
      background: disabled ? '#D1D5DB' : '#611208',
      color: '#fff',
      border: 'none',
      borderRadius: '12px',
      fontSize: '14px',
      fontWeight: 500,
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'all 150ms ease',
      opacity: disabled ? 0.6 : 1,
      height: '48px'
    })
  }

  const [isMobile, setIsMobile] = useState(window.innerWidth < 900)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 900)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div style={{
      ...styles.wrapper,
      flexDirection: isMobile ? 'column' : 'row',
      width: isMobile ? '100%' : '80%'
    }}>
      {!isMobile && (
        <div style={styles.sidebar}>
          <div style={styles.sidebarCard}>
            <div style={styles.sidebarTitle}>
              <CalendarIcon />
              选择日期
            </div>
            <input
              type="date"
              value={selectedDate}
              onChange={handleDateChange}
              max={getTodayString()}
              style={{
                width: '100%',
                padding: '8px 10px',
                border: '1px solid #E5E7EB',
                borderRadius: '6px',
                fontSize: '13px',
                outline: 'none',
                cursor: 'pointer',
                background: '#FAFAFA'
              }}
            />
            {!isToday && (
              <div style={{
                marginTop: '8px',
                padding: '8px 10px',
                background: '#FEF3C7',
                borderRadius: '6px',
                fontSize: '12px',
                color: '#92400E'
              }}>
                正在补录 {selectedDate} 的日记
              </div>
            )}
          </div>
          <div style={styles.sidebarCard}>
            <div style={styles.sidebarTitle}>
              <ChatIcon />
              对话统计
            </div>
            <div style={styles.sidebarText}>
              已记录 {messages.filter(m => m.role === 'user').length} 条消息
            </div>
          </div>
          <div style={styles.sidebarCardLarge}>
            <div style={styles.sidebarTitle}>
              <SparkleIcon />
              使用提示
            </div>
            <div style={styles.sidebarText}>
              我是小年，你的编年日记助手。通过对话帮你记录每一天的心情和故事。尽情分享你的想法，我会帮你整理成日记。
            </div>
          </div>
          <button
            onClick={handleGenerateDiary}
            disabled={generatingDiary || messages.length === 0}
            style={{
              ...styles.button(generatingDiary || messages.length === 0),
              width: '100%',
              marginTop: '4px'
            }}
          >
            {generatingDiary ? '生成中...' : (todayDiary ? '重新生成日记' : `生成${isToday ? '今日' : '该日'}日记`)}
          </button>
          {todayDiary && (
            <button
              onClick={handleViewDiary}
              style={{
                ...styles.button(false),
                width: '100%',
                marginTop: '8px',
                background: '#10B981'
              }}
            >
              查看{isToday ? '今日' : '该日'}日记
            </button>
          )}
        </div>
      )}

      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>编年</h1>
          <p style={styles.subtitle}>记录每一天的温暖时刻</p>
        </div>

        <div style={{
          ...styles.messages,
          scrollbarWidth: 'none',
          msOverflowStyle: 'none'
        }}>
          {messages.length === 0 && (
            <div style={styles.empty}>
              <p>你好！我是小年，你的编年日记助手</p>
              <p style={{marginTop: '8px'}}>今天有什么想分享的吗？</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                ...styles.bubble,
                ...(m.role === 'user' ? styles.userBubble : styles.aiBubble)
              }}
            >
              {m.role === 'user' ? (
                m.content
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
              )}
            </div>
          ))}
          {loading && <div style={styles.loading}>正在输入...</div>}
          <div ref={bottomRef} />
        </div>

        <div style={styles.inputArea}>
          <div style={{ flex: 1, position: 'relative' }}>
            {hasPendingMessage && (
              <div style={{
                position: 'absolute',
                bottom: '100%',
                left: 0,
                right: 0,
                padding: '8px 12px',
                background: '#FEF3C7',
                border: '1px solid #FCD34D',
                borderRadius: '8px 8px 0 0',
                fontSize: '13px',
                color: '#92400E',
                marginBottom: '4px',
                maxHeight: '80px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                <div style={{ fontSize: '11px', marginBottom: '4px', opacity: 0.8 }}>
                  AI 回复完成后将自动发送：
                </div>
                {pendingInput}
              </div>
            )}
            <textarea
              ref={inputRef}
              style={{
                ...styles.input,
                scrollbarWidth: 'none',
                msOverflowStyle: 'none',
                width: '100%'
              }}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              placeholder={loading 
                ? "AI 回复中，你可以继续输入... (Enter 暂存，Shift+Enter 换行)" 
                : "今天有什么想分享的... (Enter 发送，Shift+Enter 换行)"
              }
              disabled={false}
              rows={1}
            />
          </div>
          {loading ? (
            <button
              style={{
                ...styles.button(false),
                background: '#DC2626',
                minWidth: '70px'
              }}
              onClick={handleStop}
            >
              停止
            </button>
          ) : (
            <button
              style={styles.button(!input.trim())}
              onClick={() => handleSend()}
              disabled={!input.trim()}
            >
              发送
            </button>
          )}
        </div>
      </div>

      {showDiaryModal && todayDiary && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }} onClick={() => setShowDiaryModal(false)}>
          <div style={{
            background: '#fff',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '600px',
            width: '100%',
            maxHeight: '80vh',
            overflow: 'auto',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
              paddingBottom: '12px',
              borderBottom: '1px solid #F3F4F6'
            }}>
              <h2 style={{ margin: 0, fontSize: '18px', color: '#1A1A1A' }}>
                <BookIcon /> {todayDiary.date} 的日记
              </h2>
              <button
                onClick={() => setShowDiaryModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#9CA3AF'
                }}
              >
                ×
              </button>
            </div>

            {todayDiary.mood && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '16px',
                padding: '12px 16px',
                background: '#F9FAFB',
                borderRadius: '8px'
              }}>
                <span style={{ fontSize: '28px' }}>
                  {MOOD_CONFIG[todayDiary.mood.level]?.icon}
                </span>
                <div>
                  <div style={{ fontWeight: 600, color: '#1A1A1A' }}>
                    {MOOD_CONFIG[todayDiary.mood.level]?.name || todayDiary.mood.name}
                  </div>
                  {todayDiary.mood.description && (
                    <div style={{ fontSize: '13px', color: '#6B7280' }}>
                      {todayDiary.mood.description}
                    </div>
                  )}
                </div>
              </div>
            )}

            {todayDiary.tags && todayDiary.tags.length > 0 && (
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '6px',
                marginBottom: '16px'
              }}>
                {todayDiary.tags.map(tag => (
                  <span key={tag} style={{
                    padding: '4px 10px',
                    background: '#F3F4F6',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#4B5563'
                  }}>
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            <div style={{
              fontSize: '15px',
              lineHeight: 1.8,
              color: '#1A1A1A',
              whiteSpace: 'pre-wrap'
            }}>
              {todayDiary.content}
            </div>

            <div style={{
              marginTop: '20px',
              paddingTop: '12px',
              borderTop: '1px solid #F3F4F6',
              fontSize: '12px',
              color: '#9CA3AF'
            }}>
              基于 {todayDiary.conversation_count || messages.length} 条对话生成
            </div>
          </div>
        </div>
      )}

      <Dialog {...dialog} />
    </div>
  )
}
