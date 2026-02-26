import React from 'react'

const Dialog = ({
  isOpen,
  title,
  message,
  type = 'info',
  confirmText = '确定',
  cancelText = '取消',
  onConfirm,
  onCancel,
  showCancel = false
}) => {
  if (!isOpen) return null

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    confirm: '❓',
    info: 'ℹ️'
  }

  const colors = {
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    confirm: '#3B82F6',
    info: '#6B7280'
  }

  return (
    <div style={styles.overlay} onClick={onCancel}>
      <div style={styles.container} onClick={e => e.stopPropagation()}>
        <div style={{ ...styles.icon, color: colors[type] }}>
          {icons[type]}
        </div>
        <h3 style={styles.title}>{title}</h3>
        <p style={styles.message}>{message}</p>
        <div style={styles.actions}>
          {showCancel && (
            <button style={styles.cancelBtn} onClick={onCancel}>
              {cancelText}
            </button>
          )}
          <button
            style={{ ...styles.confirmBtn, backgroundColor: colors[type] }}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

const styles = {
  overlay: {
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
    animation: 'fadeIn 0.2s ease'
  },
  container: {
    background: '#fff',
    padding: '32px',
    borderRadius: '16px',
    maxWidth: '400px',
    width: '90%',
    textAlign: 'center',
    boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
    animation: 'slideUp 0.3s ease'
  },
  icon: {
    fontSize: '48px',
    marginBottom: '16px'
  },
  title: {
    fontSize: '20px',
    fontWeight: 600,
    marginBottom: '12px',
    color: '#1A1A1A'
  },
  message: {
    fontSize: '15px',
    color: '#6B7280',
    lineHeight: 1.6,
    marginBottom: '24px'
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center'
  },
  cancelBtn: {
    padding: '12px 24px',
    background: '#F3F4F6',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 500,
    color: '#6B7280',
    transition: 'all 150ms ease'
  },
  confirmBtn: {
    padding: '12px 24px',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 500,
    color: '#fff',
    transition: 'all 150ms ease'
  }
}

export default Dialog
