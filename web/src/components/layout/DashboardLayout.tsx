import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import styles from './DashboardLayout.module.css'

type Props = {
  children: ReactNode
  rightPanel?: ReactNode
}

export default function DashboardLayout({ children, rightPanel }: Props) {
  return (
    <div className={styles.root}>
      <Sidebar />
      <main className={styles.main}>{children}</main>
      {rightPanel != null && (
        <div className={styles.rightPanel}>{rightPanel}</div>
      )}
    </div>
  )
}
