import React, { useState, useEffect } from 'react'
import { setConfig, getConfig, analyzeWritingStyle, getUserStyle, saveUserStyle } from '../utils/api'

const CpuIcon = ({solid}) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill={solid ? "currentColor" : "none"} viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px', color: solid ? '#611208' : '#6B7280'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18.75h.008v.008h-.008v-.008zm0 18.75h.008v.008h-.008v-.008zm-9 0h.008v.008h-.008v-.008zm0-18.75h.008v.008h-.008v-.008z" />
  </svg>
)

const PenIcon = ({solid}) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill={solid ? "currentColor" : "none"} viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px', color: solid ? '#611208' : '#6B7280'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
  </svg>
)

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{width: '20px', height: '20px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
  </svg>
)

export default function ConfigPage({ userId }) {
  const [activeTab, setActiveTab] = useState('llm')
  const [config, setConfigState] = useState({ provider: '', base_url: '', api_key: '', model: '', thinking: false })
  const [writingStyle, setWritingStyle] = useState('')
  const [saveStatus, setSaveStatus] = useState({ llm: false, style: false })
  const [analyzing, setAnalyzing] = useState(false)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 900)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 900)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    Promise.all([
      getConfig(userId),
      getUserStyle(userId)
    ]).then(([c, s]) => {
      if (c.provider) {
        setConfigState({
          provider: c.provider || '',
          base_url: c.base_url || '',
          api_key: c.api_key || '',
          model: c.model || '',
          thinking: c.thinking || false
        })
      }
      if (s.content) setWritingStyle(s.content)
    })
  }, [userId])

  const handleSaveLLM = async () => {
    await setConfig(userId, config)
    setSaveStatus(prev => ({ ...prev, llm: true }))
    setTimeout(() => setSaveStatus(prev => ({ ...prev, llm: false })), 2000)
  }

  const handleSaveStyle = async () => {
    await saveUserStyle(userId, writingStyle)
    setSaveStatus(prev => ({ ...prev, style: true }))
    setTimeout(() => setSaveStatus(prev => ({ ...prev, style: false })), 2000)
  }

  const handleAnalyzeStyle = async () => {
    setAnalyzing(true)
    try {
      const result = await analyzeWritingStyle(userId)
      if (result.ok && result.style) {
        // 重新获取完整的写作风格内容
        const styleRes = await getUserStyle(userId)
        if (styleRes.content) {
          setWritingStyle(styleRes.content)
        }
        alert('风格分析完成！')
      } else {
        alert(result.message || '分析失败')
      }
    } catch (e) {
      alert('分析失败：' + e.message)
    }
    setAnalyzing(false)
  }

  const tabs = [
    { id: 'llm', label: 'LLM配置', icon: CpuIcon },
    { id: 'style', label: '写作风格', icon: PenIcon }
  ]

  const styles = {
    container: {
      display: 'flex',
      gap: '24px',
      minHeight: 'calc(100vh - 112px)'
    },
    sidebar: {
      width: isMobile ? '100%' : '240px',
      flexShrink: 0
    },
    sidebarItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '14px 16px',
      marginBottom: '8px',
      borderRadius: '10px',
      cursor: 'pointer',
      transition: 'all 150ms ease',
      fontSize: '15px',
      fontWeight: 500,
      color: '#6B7280'
    },
    sidebarItemActive: {
      background: 'rgba(97, 18, 8, 0.08)',
      color: '#611208',
      fontWeight: 600
    },
    content: {
      flex: 1,
      minWidth: 0
    },
    card: {
      background: '#fff',
      padding: '32px',
      borderRadius: '16px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
    },
    title: {
      fontSize: '22px',
      fontWeight: 700,
      color: '#1A1A1A',
      marginBottom: '8px'
    },
    subtitle: {
      fontSize: '14px',
      color: '#9CA3AF',
      marginBottom: '32px'
    },
    field: {
      marginBottom: '24px'
    },
    label: {
      display: 'block',
      fontSize: '14px',
      fontWeight: 500,
      color: '#374151',
      marginBottom: '8px'
    },
    input: {
      width: '100%',
      padding: '14px 16px',
      border: '1px solid #E5E7EB',
      borderRadius: '10px',
      fontSize: '15px',
      outline: 'none',
      transition: 'all 150ms ease',
      background: '#FAFAFA'
    },
    textarea: {
      width: '100%',
      padding: '14px 16px',
      border: '1px solid #E5E7EB',
      borderRadius: '10px',
      fontSize: '15px',
      outline: 'none',
      transition: 'all 150ms ease',
      background: '#FAFAFA',
      minHeight: '120px',
      resize: 'vertical',
      fontFamily: 'inherit'
    },
    checkboxLabel: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      fontSize: '14px',
      color: '#4B5563',
      cursor: 'pointer',
      padding: '8px 0'
    },
    checkbox: {
      width: '18px',
      height: '18px',
      accentColor: '#611208'
    },
    button: {
      padding: '14px 28px',
      background: '#611208',
      color: '#fff',
      border: 'none',
      borderRadius: '10px',
      fontSize: '15px',
      fontWeight: 600,
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      transition: 'all 150ms ease',
      boxShadow: '0 4px 12px rgba(97, 18, 8, 0.2)'
    },
    buttonSecondary: {
      padding: '10px 20px',
      background: '#10B981',
      color: '#fff',
      border: 'none',
      borderRadius: '8px',
      fontSize: '14px',
      fontWeight: 500,
      cursor: 'pointer',
      transition: 'all 150ms ease'
    },
    buttonDisabled: {
      background: '#9CA3AF',
      cursor: 'not-allowed'
    },
    buttonContainer: {
      display: 'flex',
      justifyContent: 'flex-end',
      marginTop: '32px',
      paddingTop: '24px',
      borderTop: '1px solid #F3F4F6'
    },
    tipsCard: {
      marginTop: '24px',
      padding: '20px',
      background: '#F9FAFB',
      borderRadius: '12px',
      border: '1px solid #E5E7EB'
    },
    tipsTitle: {
      fontSize: '14px',
      fontWeight: 600,
      color: '#611208',
      marginBottom: '12px'
    },
    tipsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '12px'
    },
    tipItem: {
      fontSize: '13px',
      color: '#6B7280',
      lineHeight: 1.5
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.sidebar}>
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <div
              key={tab.id}
              style={{
                ...styles.sidebarItem,
                ...(activeTab === tab.id ? styles.sidebarItemActive : {})
              }}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon solid={activeTab === tab.id} />
              {tab.label}
            </div>
          )
        })}
      </div>

      <div style={styles.content}>
        {activeTab === 'llm' && (
          <div style={styles.card}>
            <h1 style={styles.title}>LLM 配置</h1>
            <p style={styles.subtitle}>配置 AI 模型服务提供商信息</p>

            <div style={styles.field}>
              <label style={styles.label}>服务商</label>
              <input
                style={styles.input}
                value={config.provider}
                onChange={e => setConfigState({...config, provider: e.target.value})}
                placeholder="如：OpenAI、千问、Llama本地"
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Base URL</label>
              <input
                style={styles.input}
                value={config.base_url}
                onChange={e => setConfigState({...config, base_url: e.target.value})}
                placeholder="如：https://api.openai.com/v1"
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>API Key</label>
              <input
                style={styles.input}
                type="password"
                value={config.api_key}
                onChange={e => setConfigState({...config, api_key: e.target.value})}
                placeholder="留空则保留原密钥"
              />
              <span style={{fontSize: '12px', color: '#9CA3AF', marginTop: '4px', display: 'block'}}>
                留空则保留原密钥，不重新加密保存
              </span>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>模型名称</label>
              <input
                style={styles.input}
                value={config.model}
                onChange={e => setConfigState({...config, model: e.target.value})}
                placeholder="如：gpt-4o、qwen-plus、llama3"
              />
            </div>

            <div style={styles.field}>
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  style={styles.checkbox}
                  checked={config.thinking}
                  onChange={e => setConfigState({...config, thinking: e.target.checked})}
                />
                支持深度思考（如 o1-mini）
              </label>
            </div>

            <div style={styles.tipsCard}>
              <div style={styles.tipsTitle}>常用配置参考</div>
              <div style={styles.tipsGrid}>
                <div style={styles.tipItem}>
                  <strong>OpenAI</strong><br/>
                  URL: api.openai.com/v1<br/>
                  模型: gpt-4o
                </div>
                <div style={styles.tipItem}>
                  <strong>阿里千问</strong><br/>
                  URL: dashscope.aliyuncs.com<br/>
                  模型: qwen-plus
                </div>
                <div style={styles.tipItem}>
                  <strong>本地 Ollama</strong><br/>
                  URL: localhost:11434/v1<br/>
                  模型: llama3
                </div>
              </div>
            </div>

            <div style={styles.buttonContainer}>
              <button style={styles.button} onClick={handleSaveLLM}>
                {saveStatus.llm && <CheckIcon />}
                {saveStatus.llm ? '已保存' : '保存LLM配置'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'style' && (
          <div style={styles.card}>
            <h1 style={styles.title}>写作风格</h1>
            <p style={styles.subtitle}>设置AI写日记时模仿你的写作风格</p>

            <div style={styles.field}>
              <label style={styles.label}>风格描述</label>
              <textarea
                style={styles.textarea}
                value={writingStyle}
                onChange={e => setWritingStyle(e.target.value)}
                placeholder="例如：简洁直接、幽默风趣、感性细腻、理性客观..."
              />
              <span style={{fontSize: '12px', color: '#9CA3AF', marginTop: '4px', display: 'block'}}>
                描述你的语言特点、句式风格、表达习惯和情感倾向等
              </span>
            </div>

            <div style={{...styles.field, marginTop: '16px'}}>
              <button
                onClick={handleAnalyzeStyle}
                disabled={analyzing}
                style={{
                  ...styles.buttonSecondary,
                  ...(analyzing ? styles.buttonDisabled : {})
                }}
              >
                {analyzing ? '分析中...' : '自动分析我的风格'}
              </button>
              <span style={{fontSize: '12px', color: '#9CA3AF', marginLeft: '12px', verticalAlign: 'middle'}}>
                基于你的历史对话记录自动分析写作风格
              </span>
            </div>

            <div style={styles.tipsCard}>
              <div style={styles.tipsTitle}>风格维度参考</div>
              <div style={styles.tipsGrid}>
                <div style={styles.tipItem}>
                  <strong>语言特点</strong><br/>
                  正式/随意/幽默/感性等
                </div>
                <div style={styles.tipItem}>
                  <strong>句式风格</strong><br/>
                  短句/长句/排比等
                </div>
                <div style={styles.tipItem}>
                  <strong>情感倾向</strong><br/>
                  积极/消极/中性等
                </div>
              </div>
            </div>

            <div style={styles.buttonContainer}>
              <button style={styles.button} onClick={handleSaveStyle}>
                {saveStatus.style && <CheckIcon />}
                {saveStatus.style ? '已保存' : '保存风格设置'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
