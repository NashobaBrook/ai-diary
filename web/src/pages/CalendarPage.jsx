import React, { useState, useEffect } from 'react'
import { getCalendar, getDiary, generateDiary, updateDiary, regenerateDiary } from '../utils/api'
import Dialog from '../components/Dialog'
import { useDialog } from '../hooks/useDialog'
import dayjs from 'dayjs'

// 心情配置
const MOOD_CONFIG = {
  1: { icon: '😢', name: '沮丧', bgColor: '#E5E7EB', borderColor: '#9CA3AF', textColor: '#4B5563' },
  2: { icon: '😕', name: '不高兴', bgColor: '#F3F4F6', borderColor: '#D1D5DB', textColor: '#6B7280' },
  3: { icon: '🙂', name: '正常', bgColor: '#FEF3C7', borderColor: '#FCD34D', textColor: '#D97706' },
  4: { icon: '😄', name: '有点喜悦', bgColor: '#FDE68A', borderColor: '#F59E0B', textColor: '#B45309' },
  5: { icon: '🥳', name: '超开心', bgColor: '#FED7AA', borderColor: '#F97316', textColor: '#C2410C' }
}

export default function CalendarPage({ userId }) {
  const [year, setYear] = useState(dayjs().year())
  const [month, setMonth] = useState(dayjs().month() + 1)
  const [calendar, setCalendar] = useState({})
  const [hoveredDay, setHoveredDay] = useState(null)
  const [selectedDiary, setSelectedDiary] = useState(null)
  const [editingDiary, setEditingDiary] = useState(null)
  const [loading, setLoading] = useState(false)
  const { dialog, showSuccess, showError, showConfirm } = useDialog()

  useEffect(() => {
    loadCalendar()
  }, [year, month])

  const loadCalendar = async () => {
    setLoading(true)
    try {
      const data = await getCalendar(userId, year, month)
      setCalendar(data.days || {})
    } catch (e) {
      showError('日历数据加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const daysInMonth = dayjs(`${year}-${month}-01`).daysInMonth()
  const firstDay = dayjs(`${year}-${month}-01`).day()

  const handleDayClick = async (day) => {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const dayData = calendar[date]

    if (!dayData) return

    if (dayData.has_diary) {
      // 有日记，查看详情
      try {
        const diary = await getDiary(userId, date)
        setSelectedDiary(diary)
      } catch (e) {
        showError('获取日记详情失败')
      }
    } else if (dayData.has_conversation) {
      // 有对话无日记，提示生成
      const confirmed = await showConfirm({
        title: '生成日记',
        message: `${date} 有对话记录但未生成日记，是否现在生成？`,
        confirmText: '生成日记',
        cancelText: '稍后再说'
      })

      if (confirmed) {
        await handleGenerateDiary(date)
      }
    }
  }

  const handleGenerateDiary = async (date) => {
    try {
      const res = await generateDiary(userId, date)
      showSuccess(res.message || '日记生成成功')
      // 刷新日历
      await loadCalendar()
      // 显示生成的日记
      setSelectedDiary(res.diary)
    } catch (e) {
      const message = e.response?.data?.message || '生成失败'
      showError(message)
    }
  }

  const handleDayHover = (day) => {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    if (calendar[date]) {
      setHoveredDay(date)
    }
  }

  // 计算统计信息
  const diaryCount = Object.values(calendar).filter(d => d?.has_diary).length
  const conversationCount = Object.values(calendar).filter(d => d?.has_conversation).length
  const pendingCount = Object.values(calendar).filter(d => d?.has_conversation && !d?.has_diary).length

  const getDayStyle = (day) => {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const dayData = calendar[date]
    const isHovered = hoveredDay === date

    if (!dayData) {
      return {
        ...styles.day,
        background: '#F9FAFB',
        color: '#9CA3AF',
        cursor: 'default'
      }
    }

    if (dayData.has_diary && dayData.mood_level) {
      const config = MOOD_CONFIG[dayData.mood_level]
      return {
        ...styles.day,
        background: config.bgColor,
        border: `2px solid ${config.borderColor}`,
        color: config.textColor,
        transform: isHovered ? 'scale(1.05)' : 'scale(1)',
        boxShadow: isHovered ? '0 4px 12px rgba(0,0,0,0.15)' : '0 2px 4px rgba(0,0,0,0.05)'
      }
    }

    if (dayData.has_conversation && !dayData.has_diary) {
      return {
        ...styles.day,
        background: '#F5F3FF',
        border: '2px dashed #A78BFA',
        color: '#7C3AED',
        transform: isHovered ? 'scale(1.05)' : 'scale(1)'
      }
    }

    return styles.day
  }

  const renderDay = (day) => {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const dayData = calendar[date]
    const style = getDayStyle(day)

    return (
      <div
        key={day}
        onClick={() => handleDayClick(day)}
        onMouseEnter={() => handleDayHover(day)}
        onMouseLeave={() => setHoveredDay(null)}
        style={style}
      >
        <span style={styles.dayNumber}>{day}</span>
        {dayData?.has_diary && dayData?.mood_level && (
          <span style={styles.moodIcon}>{MOOD_CONFIG[dayData.mood_level].icon}</span>
        )}
        {dayData?.has_conversation && !dayData?.has_diary && (
          <span style={styles.pendingBadge}>待生成</span>
        )}
      </div>
    )
  }

  // 响应式处理
  const [isMobile, setIsMobile] = useState(window.innerWidth < 900)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 900)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div style={{
      ...styles.wrapper,
      flexDirection: isMobile ? 'column' : 'row'
    }}>
      <div style={{
        ...styles.main,
        padding: isMobile ? '20px' : '32px'
      }}>
        <div style={styles.header}>
          <h1 style={styles.title}>日历</h1>
          <div style={styles.nav}>
            <button onClick={() => setMonth(m => m === 1 ? 12 : m - 1)} style={styles.navBtn}>◀</button>
            <span style={styles.date}>{year}年{month}月</span>
            <button onClick={() => setMonth(m => m === 12 ? 1 : m + 1)} style={styles.navBtn}>▶</button>
          </div>
        </div>

        {/* 图例 */}
        <div style={styles.legend}>
          <div style={styles.legendItem}>
            <span style={{ ...styles.legendColor, background: '#FDE68A', border: '2px solid #F59E0B' }}></span>
            <span style={styles.legendText}>有日记</span>
          </div>
          <div style={styles.legendItem}>
            <span style={{ ...styles.legendColor, background: '#F5F3FF', border: '2px dashed #A78BFA' }}></span>
            <span style={styles.legendText}>有对话未生成</span>
          </div>
        </div>

        <div style={styles.calendar}>
          {['日', '一', '二', '三', '四', '五', '六'].map(d => (
            <div key={d} style={styles.weekday}>{d}</div>
          ))}
          {Array(firstDay).fill(null).map((_, i) => <div key={`empty-${i}`} style={styles.emptyDay} />)}
          {Array(daysInMonth).fill(0).map((_, i) => renderDay(i + 1))}
        </div>
      </div>

      {!isMobile && (
        <div style={styles.sidebar}>
          <div style={styles.sidebarCard}>
            <div style={styles.statCard}>
              <div style={styles.statIcon}>📖</div>
              <div style={styles.statContent}>
                <div style={styles.statValue}>{diaryCount}</div>
                <div style={styles.statLabel}>本月日记</div>
              </div>
            </div>
          </div>
          <div style={styles.sidebarCard}>
            <div style={styles.statCard}>
              <div style={styles.statIcon}>💬</div>
              <div style={styles.statContent}>
                <div style={styles.statValue}>{conversationCount}</div>
                <div style={styles.statLabel}>对话天数</div>
              </div>
            </div>
          </div>
          {pendingCount > 0 && (
            <div style={styles.sidebarCard}>
              <div style={styles.statCard}>
                <div style={{ ...styles.statIcon, background: 'rgba(139, 92, 246, 0.1)' }}>⏳</div>
                <div style={styles.statContent}>
                  <div style={{ ...styles.statValue, color: '#8B5CF6' }}>{pendingCount}</div>
                  <div style={styles.statLabel}>待生成日记</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 日记详情弹窗 */}
      {selectedDiary && (
        <div style={styles.modal} onClick={() => setSelectedDiary(null)}>
          <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h3 style={styles.modalTitle}>{selectedDiary.date}</h3>
              <div style={styles.headerActions}>
                <button
                  style={styles.editBtn}
                  onClick={() => {
                    setEditingDiary(selectedDiary)
                    setSelectedDiary(null)
                  }}
                >
                  编辑
                </button>
                {selectedDiary.mood && (
                  <div style={styles.moodDisplay}>
                    <span style={styles.moodIconLarge}>
                      {MOOD_CONFIG[selectedDiary.mood.level]?.icon}
                    </span>
                    <span style={styles.moodName}>{selectedDiary.mood.name}</span>
                  </div>
                )}
              </div>
            </div>

            {selectedDiary.tags && selectedDiary.tags.length > 0 && (
              <div style={styles.tagsContainer}>
                {selectedDiary.tags.map(tag => (
                  <span key={tag} style={styles.tag}>#{tag}</span>
                ))}
              </div>
            )}

            <div style={styles.modalText}>{selectedDiary.content}</div>

            {selectedDiary.mood?.description && (
              <div style={styles.moodDescription}>
                💭 {selectedDiary.mood.description}
              </div>
            )}

            <button style={styles.closeBtn} onClick={() => setSelectedDiary(null)}>关闭</button>
          </div>
        </div>
      )}

      {/* 日记编辑弹窗 */}
      {editingDiary && (
        <DiaryEditModal
          diary={editingDiary}
          onSave={async (data) => {
            try {
              const result = await updateDiary(userId, editingDiary.date, data)
              if (result.success) {
                showSuccess('日记保存成功')
                setEditingDiary(null)
                loadCalendar()
              } else {
                showError(result.message || '保存失败')
              }
            } catch (e) {
              showError('保存失败，请稍后重试')
            }
          }}
          onRegenerate={async () => {
            try {
              const confirmed = await showConfirm({
                title: '重新生成',
                message: '确定要重新生成这篇日记吗？这将覆盖当前内容。',
                confirmText: '重新生成',
                cancelText: '取消'
              })
              if (confirmed) {
                const result = await regenerateDiary(userId, editingDiary.date)
                if (result.success) {
                  showSuccess('日记重新生成成功')
                  setEditingDiary(null)
                  loadCalendar()
                } else {
                  showError(result.message || '重新生成失败')
                }
              }
            } catch (e) {
              showError('重新生成失败，请稍后重试')
            }
          }}
          onCancel={() => setEditingDiary(null)}
        />
      )}

      {/* 弹窗组件 */}
      <Dialog {...dialog} />
    </div>
  )
}

// 日记编辑弹窗组件
function DiaryEditModal({ diary, onSave, onRegenerate, onCancel }) {
  const [content, setContent] = useState(diary.content || '')
  const [moodLevel, setMoodLevel] = useState(diary.mood?.level || 3)
  const [tags, setTags] = useState((diary.tags || []).join(', '))
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    await onSave({
      content,
      mood: {
        level: moodLevel,
        ...MOOD_CONFIG[moodLevel]
      },
      tags: tags.split(',').map(t => t.trim()).filter(Boolean)
    })
    setSaving(false)
  }

  return (
    <div style={styles.modal} onClick={onCancel}>
      <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>编辑日记 - {diary.date}</h3>
        </div>

        {/* 心情选择器 */}
        <div style={styles.editSection}>
          <label style={styles.editLabel}>心情</label>
          <div style={styles.moodSelector}>
            {Object.entries(MOOD_CONFIG).map(([level, config]) => (
              <button
                key={level}
                style={{
                  ...styles.moodBtn,
                  background: moodLevel === Number(level) ? config.bgColor : '#f5f5f5',
                  border: moodLevel === Number(level) ? `2px solid ${config.borderColor}` : '2px solid transparent'
                }}
                onClick={() => setMoodLevel(Number(level))}
              >
                {config.icon} {config.name}
              </button>
            ))}
          </div>
        </div>

        {/* 标签编辑 */}
        <div style={styles.editSection}>
          <label style={styles.editLabel}>标签</label>
          <input
            style={styles.tagInput}
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="用逗号分隔多个标签"
          />
        </div>

        {/* 内容编辑 */}
        <div style={styles.editSection}>
          <label style={styles.editLabel}>日记内容</label>
          <textarea
            style={styles.contentTextarea}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={12}
            placeholder="日记内容..."
          />
        </div>

        <div style={styles.editBtnGroup}>
          <button style={styles.regenerateBtn} onClick={onRegenerate} disabled={saving}>
            重新生成
          </button>
          <div style={styles.editBtnRight}>
            <button style={styles.cancelBtn} onClick={onCancel} disabled={saving}>取消</button>
            <button style={styles.saveBtn} onClick={handleSave} disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  wrapper: {
    display: 'flex',
    gap: '24px',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  main: {
    flex: 1,
    background: '#fff',
    borderRadius: '16px',
    padding: '32px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  sidebar: {
    width: '320px',
    flexShrink: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '16px'
  },
  sidebarCard: {
    background: '#fff',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px'
  },
  title: {
    fontSize: '24px',
    fontWeight: 600,
    color: '#1A1A1A'
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px'
  },
  navBtn: {
    padding: '10px 18px',
    border: '1px solid #E5E7EB',
    background: '#fff',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '16px',
    color: '#6B7280',
    transition: 'all 150ms ease'
  },
  date: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#1A1A1A',
    minWidth: '120px',
    textAlign: 'center'
  },
  legend: {
    display: 'flex',
    gap: '20px',
    marginBottom: '20px',
    padding: '12px 16px',
    background: '#F9FAFB',
    borderRadius: '10px'
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    color: '#6B7280'
  },
  legendColor: {
    width: '20px',
    height: '20px',
    borderRadius: '4px'
  },
  legendText: {
    fontSize: '14px'
  },
  calendar: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
    gap: '12px'
  },
  weekday: {
    padding: '16px',
    textAlign: 'center',
    fontSize: '14px',
    fontWeight: 600,
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  day: {
    aspectRatio: '1',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 500,
    transition: 'all 150ms ease',
    position: 'relative',
    gap: '4px'
  },
  dayNumber: {
    fontSize: '16px',
    fontWeight: 500
  },
  moodIcon: {
    fontSize: '20px'
  },
  pendingBadge: {
    fontSize: '10px',
    color: '#8B5CF6',
    background: 'rgba(139, 92, 246, 0.1)',
    padding: '2px 6px',
    borderRadius: '10px'
  },
  emptyDay: {
    aspectRatio: '1'
  },
  modal: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 200,
    animation: 'fadeIn 0.2s ease'
  },
  modalContent: {
    background: '#fff',
    padding: '32px',
    borderRadius: '16px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '80vh',
    overflow: 'auto',
    boxShadow: '0 20px 40px rgba(0,0,0,0.2)'
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px'
  },
  modalTitle: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#1A1A1A'
  },
  moodDisplay: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    background: '#F9FAFB',
    borderRadius: '20px'
  },
  moodIconLarge: {
    fontSize: '24px'
  },
  moodName: {
    fontSize: '14px',
    fontWeight: 500,
    color: '#6B7280'
  },
  tagsContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '16px'
  },
  tag: {
    padding: '4px 12px',
    background: '#F3F4F6',
    borderRadius: '12px',
    fontSize: '13px',
    color: '#6B7280'
  },
  modalText: {
    fontSize: '15px',
    color: '#4B5563',
    lineHeight: 1.8,
    whiteSpace: 'pre-wrap'
  },
  moodDescription: {
    marginTop: '16px',
    padding: '12px 16px',
    background: '#FEF3C7',
    borderRadius: '10px',
    fontSize: '14px',
    color: '#92400E'
  },
  closeBtn: {
    marginTop: '24px',
    padding: '14px 24px',
    background: '#F3F4F6',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 500,
    color: '#6B7280',
    width: '100%',
    transition: 'all 150ms ease'
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  editBtn: {
    padding: '8px 16px',
    background: '#6366F1',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    color: '#fff',
    transition: 'all 150ms ease'
  },
  editSection: {
    marginBottom: '20px'
  },
  editLabel: {
    display: 'block',
    fontSize: '14px',
    fontWeight: 500,
    color: '#374151',
    marginBottom: '8px'
  },
  moodSelector: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap'
  },
  moodBtn: {
    padding: '8px 12px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '13px',
    transition: 'all 150ms ease'
  },
  tagInput: {
    width: '100%',
    padding: '12px',
    border: '1px solid #E5E7EB',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box'
  },
  contentTextarea: {
    width: '100%',
    padding: '12px',
    border: '1px solid #E5E7EB',
    borderRadius: '8px',
    fontSize: '14px',
    fontFamily: 'inherit',
    lineHeight: 1.6,
    resize: 'vertical',
    outline: 'none',
    boxSizing: 'border-box'
  },
  editBtnGroup: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '24px',
    gap: '12px'
  },
  editBtnRight: {
    display: 'flex',
    gap: '12px'
  },
  regenerateBtn: {
    padding: '12px 20px',
    background: '#F59E0B',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    color: '#fff',
    transition: 'all 150ms ease'
  },
  cancelBtn: {
    padding: '12px 20px',
    background: '#F3F4F6',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    color: '#6B7280',
    transition: 'all 150ms ease'
  },
  saveBtn: {
    padding: '12px 24px',
    background: '#6366F1',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    color: '#fff',
    transition: 'all 150ms ease'
  },
  statCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  statIcon: {
    width: '48px',
    height: '48px',
    borderRadius: '12px',
    background: 'rgba(97, 18, 8, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px'
  },
  statContent: {
    flex: 1
  },
  statValue: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#611208'
  },
  statLabel: {
    fontSize: '14px',
    color: '#9CA3AF'
  }
}
