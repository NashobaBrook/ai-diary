import { useState, useCallback } from 'react'

export function useDialog() {
  const [dialog, setDialog] = useState({
    isOpen: false,
    title: '',
    message: '',
    type: 'info',
    showCancel: false,
    onConfirm: null,
    onCancel: null
  })

  const showDialog = useCallback((config) => {
    setDialog({
      isOpen: true,
      showCancel: false,
      ...config
    })
  }, [])

  const showSuccess = useCallback((message, title = '成功') => {
    setDialog({
      isOpen: true,
      title,
      message,
      type: 'success',
      showCancel: false,
      onConfirm: () => setDialog(prev => ({ ...prev, isOpen: false })),
      onCancel: () => setDialog(prev => ({ ...prev, isOpen: false }))
    })
  }, [])

  const showError = useCallback((message, title = '错误') => {
    setDialog({
      isOpen: true,
      title,
      message,
      type: 'error',
      showCancel: false,
      onConfirm: () => setDialog(prev => ({ ...prev, isOpen: false })),
      onCancel: () => setDialog(prev => ({ ...prev, isOpen: false }))
    })
  }, [])

  const showConfirm = useCallback((config) => {
    return new Promise((resolve) => {
      setDialog({
        isOpen: true,
        type: 'confirm',
        showCancel: true,
        ...config,
        onConfirm: () => {
          setDialog(prev => ({ ...prev, isOpen: false }))
          resolve(true)
        },
        onCancel: () => {
          setDialog(prev => ({ ...prev, isOpen: false }))
          resolve(false)
        }
      })
    })
  }, [])

  const closeDialog = useCallback(() => {
    setDialog(prev => ({ ...prev, isOpen: false }))
  }, [])

  return {
    dialog,
    showDialog,
    showSuccess,
    showError,
    showConfirm,
    closeDialog
  }
}
