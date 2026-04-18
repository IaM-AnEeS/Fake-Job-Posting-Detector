import Link from 'next/link'
import styles from './page.module.css'

export default function Home() {
  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Hero */}
        <section className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.badgeDot}></span>
          Powered by machine learning
        </div>
        <h1 className={styles.heroTitle}>
          Detect fake job postings instantly
        </h1>
        <p className={styles.heroSub}>
          Paste any job listing and our AI model tells you if it's real
          or a scam — in seconds.
        </p>
        <div className={styles.heroBtns}>
          <Link href="/detect" className={styles.btnPrimary}>
            Analyze a job posting
          </Link>
          <a href="#how" className={styles.btnSecondary}>
            See how it works
          </a>
        </div>
        <p className={styles.heroNote}>
          Free to use · No sign-up required · 97% accuracy
        </p>
      </section>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statNum}>18,000+</span>
          <span className={styles.statLabel}>Jobs trained on</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statNum}>97.4%</span>
          <span className={styles.statLabel}>Model accuracy</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statNum}>&lt; 1s</span>
          <span className={styles.statLabel}>Detection speed</span>
        </div>
      </div>

      {/* How it works */}
      <section className={styles.section} id="how">
        <p className={styles.sectionLabel}>How it works</p>
        <h2 className={styles.sectionTitle}>Three steps to stay safe</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNum}>1</div>
            <h3 className={styles.stepTitle}>Paste the job</h3>
            <p className={styles.stepDesc}>
              Copy any job listing — title, description, company, salary, location.
            </p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>2</div>
            <h3 className={styles.stepTitle}>AI analyzes it</h3>
            <p className={styles.stepDesc}>
              Our ML model checks 15+ signals including language patterns and salary anomalies.
            </p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>3</div>
            <h3 className={styles.stepTitle}>Get your verdict</h3>
            <p className={styles.stepDesc}>
              See Real or Fake with a confidence score and breakdown of warning flags.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <h2 className={styles.sectionTitle}>What makes it accurate</h2>
        <div className={styles.featGrid}>
          <div className={styles.feat}>
            <div className={`${styles.featIcon} ${styles.iconRed}`}>⚠</div>
            <div>
              <h3 className={styles.featTitle}>Scam language detection</h3>
              <p className={styles.featDesc}>Catches vague promises, urgency tactics, and unrealistic salary claims.</p>
            </div>
          </div>
          <div className={styles.feat}>
            <div className={`${styles.featIcon} ${styles.iconGreen}`}>✓</div>
            <div>
              <h3 className={styles.featTitle}>Company credibility check</h3>
              <p className={styles.featDesc}>Analyzes company name patterns commonly used in fraudulent listings.</p>
            </div>
          </div>
          <div className={styles.feat}>
            <div className={`${styles.featIcon} ${styles.iconBlue}`}>⚙</div>
            <div>
              <h3 className={styles.featTitle}>TF-IDF + ML model</h3>
              <p className={styles.featDesc}>Trained on 18,000 real and fake postings from the EMSCAD dataset.</p>
            </div>
          </div>
          <div className={styles.feat}>
            <div className={`${styles.featIcon} ${styles.iconAmber}`}>★</div>
            <div>
              <h3 className={styles.featTitle}>Confidence score</h3>
              <p className={styles.featDesc}>Not just Fake/Real — see how confident the model is as a percentage.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Example cards */}
      <section className={styles.section}>
        <p className={styles.sectionLabel}>Examples</p>
        <h2 className={styles.sectionTitle}>Example detections</h2>
        <div className={styles.sampleCards}>
          <div className={styles.sampleCard}>
            <div className={styles.cardTop}>
              <span className={styles.cardTitle}>Data Entry Clerk — Work from Home</span>
              <span className={`${styles.badge2} ${styles.fake}`}>Fake</span>
            </div>
            <p className={styles.cardCompany}>Unknown Corp · Remote · $5,000/week</p>
            <p className={styles.cardDesc}>No experience needed. Earn $5,000 weekly processing orders. Immediate start...</p>
            <div className={styles.confBar}>
              <p className={styles.confLabel}>Confidence: 94%</p>
              <div className={styles.barBg}>
                <div className={`${styles.bar} ${styles.barFake}`} style={{width: '94%'}}></div>
              </div>
            </div>
          </div>

          <div className={styles.sampleCard}>
            <div className={styles.cardTop}>
              <span className={styles.cardTitle}>Frontend Engineer — React</span>
              <span className={`${styles.badge2} ${styles.real}`}>Real</span>
            </div>
            <p className={styles.cardCompany}>Stripe · San Francisco, CA · $130k–$160k</p>
            <p className={styles.cardDesc}>3+ years React experience. You'll work on our payment UI team building...</p>
            <div className={styles.confBar}>
              <p className={styles.confLabel}>Confidence: 98%</p>
              <div className={styles.barBg}>
                <div className={`${styles.bar} ${styles.barReal}`} style={{width: '98%'}}></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={styles.cta}>
        <h2 className={styles.ctaTitle}>Ready to check a job posting?</h2>
        <p className={styles.ctaSub}>Paste any listing and get an answer in under a second.</p>
        <Link href="/detect" className={styles.btnPrimary}>
          Analyze a job now
        </Link>
      </section>
      </div>
    </div>
  )
}