import React, { useState, useEffect } from 'react'
import { getStats, getDiaries } from '../utils/api'

const BookIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '28px', height: '28px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
  </svg>
)

const CalendarIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '28px', height: '28px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18-0v-1.5m0 1.5v-1.5m0 0l1.5 1.5m-1.5-1.5l1.5-1.5" />
  </svg>
)

const FireIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '28px', height: '28px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 006.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48c1.028-.872 2.266-1.737 3.643-1.737 1.855 0 3.05 1.412 3.435 2.857z" />
  </svg>
)

const FaceSmileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '28px', height: '28px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
  </svg>
)

const SparkleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
  </svg>
)

export default function StatsPage({ userId }) {
  const [stats, setStats] = useState({ total_diaries: 0, this_month_count: 0, mood_distribution: {} })
  const [diaries, setDiaries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
    loadDiaries()
  }, [userId])

  const loadStats = async () => {
    try {
      const s = await getStats(userId)
      setStats(s)
    } catch (e) {
      console.error('加载统计失败:', e)
    }
  }

  const loadDiaries = async () => {
    try {
      const d = await getDiaries(userId)
      setDiaries(d || [])
    } catch (e) {
      console.error('加载日记失败:', e)
    }
    setLoading(false)
  }

  const generateInsight = () => {
    if (stats.total_diaries === 0) {
      return "开始记录你的第一篇日记，开启自我探索之旅。"
    }

    const moods = Object.entries(stats.mood_distribution)
    if (moods.length === 0) {
      return `你已经记录了 ${stats.total_diaries} 篇日记，继续坚持，发现更多关于自己的故事。`
    }

    const sortedMoods = moods.sort((a, b) => b[1] - a[1])
    const dominantMood = sortedMoods[0]
    const dominantCount = dominantMood[1]
    const dominantPercent = Math.round((dominantCount / stats.total_diaries) * 100)

    const avgMood = moods.reduce((sum, [mood, count]) => {
      const level = mood === '沮丧' ? 1 : mood === '不高兴' ? 2 : mood === '正常' ? 3 : mood === '有点喜悦' ? 4 : 5
      return sum + level * count
    }, 0) / stats.total_diaries

    let insight = ""

    if (stats.total_diaries < 5) {
      insight = "刚开始记录，坚持就是胜利！继续记录，你会发现更多关于自己的故事。"
    } else if (stats.total_diaries < 10) {
      insight = "你已经养成记录习惯了，继续保持！每天的一点记录，都会成为珍贵的回忆。"
    } else if (stats.total_diaries < 30) {
      insight = `记录了 ${stats.total_diaries} 篇日记，你已经很棒了！你的主要心情是${dominantMood[0]}（占比${dominantPercent}%），${getMoodAdvice(dominantMood[0])}`
    } else {
      insight = `太棒了！你已经坚持记录了 ${stats.total_diaries} 篇日记。你的平均心情指数是 ${avgMood.toFixed(1)}，整体${getOverallMoodDescription(avgMood)}。${getStreakAdvice(stats.total_diaries)}`
    }

    return insight
  }

  const getMoodAdvice = (mood) => {
    const advices = {
      '沮丧': '试着记录一些小确幸，关注生活中的美好事物，让心情慢慢好转。',
      '不高兴': '生活中难免有不如意，记录下来也是一种释放，相信明天会更好。',
      '正常': '保持平和的心态很好，继续记录生活中的点滴变化。',
      '有点喜悦': '看来你经常有开心的事情，保持这份积极的心态！',
      '超开心': '你的生活充满了正能量，继续保持这份快乐！'
    }
    return advices[mood] || ''
  }

  const getOverallMoodDescription = (avg) => {
    if (avg < 2) return '情绪偏低'
    if (avg < 3) return '有些起伏'
    if (avg < 4) return '相对稳定'
    if (avg < 5) return '比较积极'
    return '非常乐观'
  }

  const getStreakAdvice = (count) => {
    if (count < 30) return "坚持下去，你会看到自己成长的轨迹。"
    if (count < 100) return "你正在建立长期的记录习惯，这非常有价值。"
    return "你已经成为了一个资深的记录者，这些日记将是你人生宝贵的财富。"
  }

  const styles = {
    container: {
      maxWidth: '1400px',
      margin: '0 auto'
    },
    header: {
      marginBottom: '24px'
    },
    title: {
      fontSize: '24px',
      fontWeight: 700,
      color: '#1A1A1A',
      marginBottom: '6px'
    },
    subtitle: {
      fontSize: '14px',
      color: '#9CA3AF'
    },
    loading: {
      textAlign: 'center',
      padding: '80px 0',
      color: '#9CA3AF',
      fontSize: '15px'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '16px',
      marginBottom: '24px'
    },
    card: {
      background: '#fff',
      padding: '20px',
      borderRadius: '12px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      border: '1px solid #F3F4F6',
      display: 'flex',
      alignItems: 'center',
      gap: '14px'
    },
    cardIcon: {
      width: '48px',
      height: '48px',
      borderRadius: '12px',
      background: 'rgba(97, 18, 8, 0.1)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    cardContent: {
      flex: 1
    },
    cardNum: {
      fontSize: '28px',
      fontWeight: 700,
      color: '#611208',
      lineHeight: 1.2
    },
    cardLabel: {
      fontSize: '13px',
      color: '#9CA3AF',
      marginTop: '4px'
    },
    contentGrid: {
      display: 'grid',
      gridTemplateColumns: '2fr 1fr',
      gap: '16px'
    },
    section: {
      background: '#fff',
      padding: '24px',
      borderRadius: '12px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      border: '1px solid #F3F4F6'
    },
    sectionTitle: {
      fontSize: '16px',
      fontWeight: 600,
      marginBottom: '20px',
      color: '#1A1A1A'
    },
    empty: {
      textAlign: 'center',
      color: '#9CA3AF',
      padding: '40px 0',
      fontSize: '14px'
    },
    moodItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      marginBottom: '16px'
    },
    moodLabel: {
      width: '60px',
      fontSize: '14px',
      color: '#4B5563',
      fontWeight: 500
    },
    moodBar: {
      flex: 1,
      height: '28px',
      background: '#F3F4F6',
      borderRadius: '14px',
      overflow: 'hidden'
    },
    moodFill: (percent) => ({
      height: '100%',
      background: 'linear-gradient(90deg, #611208 0%, #8B3A2A 100%)',
      borderRadius: '14px',
      width: `${percent}%`,
      transition: 'width 0.5s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-end',
      paddingRight: percent > 15 ? '10px' : '0'
    }),
    moodCount: {
      minWidth: '36px',
      textAlign: 'right',
      fontSize: '14px',
      color: '#6B7280',
      fontWeight: 600
    },
    insightCard: {
      background: 'linear-gradient(135deg, #611208 0%, #8B3A2A 100%)',
      color: '#fff',
      padding: '24px',
      borderRadius: '12px'
    },
    insightTitle: {
      fontSize: '15px',
      fontWeight: 600,
      marginBottom: '12px',
      opacity: 0.95,
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    },
    insightText: {
      fontSize: '14px',
      lineHeight: 1.7,
      opacity: 0.9
    }
  }

  const [isMobile, setIsMobile] = useState(window.innerWidth < 900)
  const [isTablet, setIsTablet] = useState(window.innerWidth < 1200)

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 900)
      setIsTablet(window.innerWidth < 1200)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  if (loading) return <div style={styles.loading}>加载中...</div>

  const moods = Object.entries(stats.mood_distribution)
  const maxMood = moods.length > 0 ? Math.max(...moods.map(([, v]) => v)) : 1

  const streak = Math.min(stats.total_diaries, 30)

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>数据统计</h1>
        <p style={styles.subtitle}>了解你的日记习惯和心情变化</p>
      </div>

      <div style={{
        ...styles.grid,
        gridTemplateColumns: isMobile ? '1fr' : isTablet ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)'
      }}>
        <div style={styles.card}>
          <div style={styles.cardIcon}><BookIcon /></div>
          <div style={styles.cardContent}>
            <div style={styles.cardNum}>{stats.total_diaries}</div>
            <div style={styles.cardLabel}>累计日记</div>
          </div>
        </div>
        <div style={styles.card}>
          <div style={styles.cardIcon}><CalendarIcon /></div>
          <div style={styles.cardContent}>
            <div style={styles.cardNum}>{stats.this_month_count}</div>
            <div style={styles.cardLabel}>本月日记</div>
          </div>
        </div>
        <div style={styles.card}>
          <div style={styles.cardIcon}><FireIcon /></div>
          <div style={styles.cardContent}>
            <div style={styles.cardNum}>{streak}</div>
            <div style={styles.cardLabel}>连续记录</div>
          </div>
        </div>
        <div style={styles.card}>
          <div style={styles.cardIcon}><FaceSmileIcon /></div>
          <div style={styles.cardContent}>
            <div style={styles.cardNum}>{moods.length}</div>
            <div style={styles.cardLabel}>心情类型</div>
          </div>
        </div>
      </div>

      <div style={{
        ...styles.contentGrid,
        gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr'
      }}>
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>心情分布</h2>
          {moods.length === 0 ? (
            <p style={styles.empty}>暂无数据，开始记录你的第一篇日记吧！</p>
          ) : (
            <div>
              {moods.map(([mood, count]) => (
                <div key={mood} style={styles.moodItem}>
                  <span style={styles.moodLabel}>{mood}</span>
                  <div style={styles.moodBar}>
                    <div style={styles.moodFill((count / maxMood) * 100)}>
                      {(count / maxMood) * 100 > 15 && (
                        <span style={{ color: '#fff', fontSize: '12px', fontWeight: 600 }}>{count}</span>
                      )}
                    </div>
                  </div>
                  <span style={styles.moodCount}>{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {!isMobile && (
          <div style={styles.insightCard}>
            <div style={styles.insightTitle}>
              <SparkleIcon />
              日记洞察
            </div>
            <div style={styles.insightText}>
              {generateInsight()}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
