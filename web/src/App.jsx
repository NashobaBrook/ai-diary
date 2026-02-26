import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import CalendarPage from './pages/CalendarPage'
import ConfigPage from './pages/ConfigPage'
import StatsPage from './pages/StatsPage'

// 使用固定用户 ID，所有用户共享数据
const USER_ID = 'default'

// 图标组件
const ChatIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.486.544.471 1.179.863 1.852 1.152 1.493.652 2.633 1.02 3.875 1.02 4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25z" />
  </svg>
)

const CalendarIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18-0v-1.5m0 1.5v-1.5m0 0l1.5 1.5m-1.5-1.5l1.5-1.5" />
  </svg>
)

const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
  </svg>
)

const CogIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{width: '20px', height: '20px'}}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.38.42l1.281 1.214c.24.231.37.569.37.928v.114c0 .358.11.683.302.946l.214 1.281c.09.542.56.941 1.11.941h2.593c.55 0 1.02-.398 1.11-.94l.213-1.281c.063-.374.313-.686.645-.87.074-.04.147-.083.22-.127.324-.196.72-.257 1.075-.124l1.217.456a1.125 1.125 0 011.38-.42l1.281 1.214c.24.231.37.569.37.928v.114c0 .358-.11.683-.302.946l-.214 1.281c-.09.542-.56.941-1.11.941h-2.593c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.063-.374-.313-.686-.645-.87-.074-.04-.147-.083-.22-.127-.324-.196-.72-.257-1.075-.124l-1.217.456a1.125 1.125 0 01-1.38-.42l-1.281-1.214c-.24-.231-.37-.569-.37-.928v-.114c0-.358.11-.683.302-.946l.214-1.281z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

function NavLink({ to, children, icon }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link to={to} style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      color: isActive ? '#611208' : '#6B7280',
      textDecoration: 'none',
      fontSize: '15px',
      fontWeight: isActive ? 600 : 500,
      padding: '10px 16px',
      borderRadius: '10px',
      background: isActive ? 'rgba(97, 18, 8, 0.08)' : 'transparent',
      transition: 'all 150ms ease',
      whiteSpace: 'nowrap'
    }}>
      {icon}
      {children}
    </Link>
  )
}

export default function App() {
  const [userId] = useState(USER_ID)

  return (
    <BrowserRouter>
      <div style={{
        minHeight: '100vh',
        background: '#F9FAFB',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* PC端顶部导航 */}
        <nav style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0 32px',
          height: '64px',
          background: '#fff',
          borderBottom: '1px solid #E5E7EB',
          position: 'sticky',
          top: 0,
          zIndex: 100
        }}>
          <div style={{
            fontSize: '20px',
            fontWeight: 700,
            color: '#611208',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <img src="/logo.png" alt="logo" style={{width: '32px', height: '32px'}} />
            编年
          </div>
          <div style={{
            display: 'flex',
            gap: '8px'
          }}>
            <NavLink to="/" icon={<ChatIcon />}>聊天</NavLink>
            <NavLink to="/calendar" icon={<CalendarIcon />}>日历</NavLink>
            <NavLink to="/stats" icon={<ChartIcon />}>统计</NavLink>
            <NavLink to="/config" icon={<CogIcon />}>设置</NavLink>
          </div>
        </nav>

        <main style={{
          flex: 1,
          padding: '24px 32px',
          maxWidth: '1400px',
          width: '100%',
          margin: '0 auto',
          boxSizing: 'border-box'
        }}>
          <Routes>
            <Route path="/" element={<ChatPage userId={userId} />} />
            <Route path="/calendar" element={<CalendarPage userId={userId} />} />
            <Route path="/stats" element={<StatsPage userId={userId} />} />
            <Route path="/config" element={<ConfigPage userId={userId} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
