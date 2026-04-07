import Link from 'next/link'
import styles from './Navbar.module.css'

export default function Navbar() {
  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.logo}>
        <span className={styles.logoDot}></span>
        JobGuard
      </Link>

      <div className={styles.links}>
        <Link href="/" className={styles.link}>Home</Link>
        <Link href="/detect" className={styles.link}>Detect</Link>
        <Link href="/about" className={styles.link}>About</Link>
      </div>

      <Link href="/detect" className={styles.ctaBtn}>
        Try it free
      </Link>
    </nav>
  )
}