/**
 * AI Diary - 设计系统配置
 * 基于 uiuxpro-max 风格指南
 */

export const designSystem = {
  // 配色方案 - 温暖现代
  colors: {
    primary: '#611208',      // 深红色 - 主色
    primaryLight: '#8B3A2A', // 浅红
    secondary: '#F5F5F5',    // 浅灰背景
    surface: '#FFFFFF',      // 卡片表面
    text: {
      primary: '#1A1A1A',    // 主文字
      secondary: '#6B7280',  // 次要文字
      muted: '#9CA3AF'       // 弱化文字
    },
    border: '#E5E7EB',       // 边框
    success: '#10B981',        // 成功
    warning: '#F59E0B',       // 警告
    error: '#EF4444'          // 错误
  },
  
  // 字体
  fonts: {
    primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"SF Mono", Monaco, Consolas, monospace'
  },
  
  // 间距
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px'
  },
  
  // 圆角
  radius: {
    sm: '6px',
    md: '12px',
    lg: '16px',
    full: '9999px'
  },
  
  // 阴影
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
  },
  
  // 过渡
  transitions: {
    fast: '150ms ease',
    normal: '250ms ease',
    slow: '350ms ease'
  }
}
