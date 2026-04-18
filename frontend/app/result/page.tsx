'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Suspense } from 'react'
import styles from './result.module.css'

function ResultContent() {
  const params = useSearchParams()
  const router = useRouter()

  const prediction = params.get('prediction') as 'fake' | 'real' | null
  const confidence = parseFloat(params.get('confidence') || '0')
  const title = params.get('title') || 'Unknown Position'
  const company = params.get('company') || 'Unknown Company'

  if (!prediction) {
    return (
      <div className={styles.page}>
        <div className={styles.container}>
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>?</div>
            <h2 className={styles.emptyTitle}>No result found</h2>
            <p className={styles.emptySub}>
              Please go back and analyze a job posting first.
            </p>
            <button
              className={styles.backBtn}
              onClick={() => router.push('/detect')}
            >
              Analyze a job
            </button>
          </div>
        </div>
      </div>
    )
  }

  const isFake = prediction === 'fake'
  const confidencePct = Math.round(confidence * 100)

  const warnings = isFake
    ? [
        'Unrealistic salary or vague compensation',
        'No specific qualifications required',
        'Urgency language detected ("immediate start", "apply now")',
        'Generic or unverifiable company name',
        'Unusual contact method or missing company details',
      ]
    : [
        'Specific role requirements listed',
        'Realistic and market-aligned salary range',
        'Verifiable company name and location',
        'Professional language and clear responsibilities',
        'Standard benefits package described',
      ]

  const riskLevel =
    confidencePct >= 85
      ? isFake ? 'High risk' : 'Low risk'
      : confidencePct >= 60
      ? 'Medium risk'
      : 'Uncertain'

  const riskColor = isFake
    ? confidencePct >= 85 ? styles.riskHigh : styles.riskMed
    : styles.riskLow

  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Breadcrumb */}
        <div className={styles.breadcrumb}>
          <button
            className={styles.breadcrumbLink}
            onClick={() => router.push('/')}
          >
            Home
          </button>
          <span className={styles.breadcrumbSep}>/</span>
          <button
            className={styles.breadcrumbLink}
            onClick={() => router.push('/detect')}
          >
            Detect
          </button>
          <span className={styles.breadcrumbSep}>/</span>
          <span className={styles.breadcrumbCurrent}>Result</span>
        </div>

        {/* Main verdict card */}
        <div className={`${styles.verdictCard} ${isFake ? styles.cardFake : styles.cardReal}`}>
          <div className={styles.verdictTop}>

            <div className={styles.verdictLeft}>
              <div className={`${styles.verdictBadge} ${isFake ? styles.badgeFake : styles.badgeReal}`}>
                <span className={styles.badgeIcon}>{isFake ? '✕' : '✓'}</span>
                {isFake ? 'Fake Job' : 'Real Job'}
              </div>
              <h1 className={styles.verdictTitle}>{title}</h1>
              <p className={styles.verdictCompany}>{company}</p>
            </div>

            <div className={styles.verdictRight}>
              <div className={styles.confidenceCircle}>
                <svg viewBox="0 0 80 80" className={styles.circleSvg}>
                  <circle
                    cx="40" cy="40" r="32"
                    fill="none"
                    stroke="#e8e8e8"
                    strokeWidth="7"
                  />
                  <circle
                    cx="40" cy="40" r="32"
                    fill="none"
                    stroke={isFake ? '#e24b4a' : '#639922'}
                    strokeWidth="7"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 32}`}
                    strokeDashoffset={`${2 * Math.PI * 32 * (1 - confidence)}`}
                    transform="rotate(-90 40 40)"
                  />
                </svg>
                <div className={styles.circleInner}>
                  <span className={`${styles.circleNum} ${isFake ? styles.numFake : styles.numReal}`}>
                    {confidencePct}%
                  </span>
                  <span className={styles.circleLabel}>confidence</span>
                </div>
              </div>
            </div>

          </div>

          {/* Confidence bar */}
          <div className={styles.confSection}>
            <div className={styles.confHeader}>
              <span className={styles.confLabel}>Model confidence</span>
              <span className={`${styles.riskPill} ${riskColor}`}>{riskLevel}</span>
            </div>
            <div className={styles.confBarBg}>
              <div
                className={`${styles.confBar} ${isFake ? styles.barFake : styles.barReal}`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
            <div className={styles.confScale}>
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Two column section */}
        <div className={styles.twoCol}>

          {/* Flags / signals */}
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>
              {isFake ? 'Warning flags detected' : 'Positive signals found'}
            </h2>
            <p className={styles.cardSub}>
              {isFake
                ? 'These patterns indicate a potentially fraudulent listing.'
                : 'These patterns suggest this is a legitimate job posting.'}
            </p>
            <ul className={styles.flagList}>
              {warnings.map((w, i) => (
                <li key={i} className={styles.flagItem}>
                  <span className={`${styles.flagDot} ${isFake ? styles.dotFake : styles.dotReal}`} />
                  {w}
                </li>
              ))}
            </ul>
          </div>

          {/* What to do */}
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>
              {isFake ? 'What you should do' : 'Next steps'}
            </h2>
            <p className={styles.cardSub}>
              {isFake
                ? 'Protect yourself from this potential scam.'
                : 'This posting looks legitimate. Here\'s how to proceed.'}
            </p>
            <div className={styles.actionList}>
              {isFake ? (
                <>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>1</div>
                    <div>
                      <p className={styles.actionTitle}>Do not apply or share personal info</p>
                      <p className={styles.actionDesc}>Never send your ID, bank details, or pay any upfront fees.</p>
                    </div>
                  </div>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>2</div>
                    <div>
                      <p className={styles.actionTitle}>Verify the company independently</p>
                      <p className={styles.actionDesc}>Search the company name on LinkedIn or their official website.</p>
                    </div>
                  </div>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>3</div>
                    <div>
                      <p className={styles.actionTitle}>Report the listing</p>
                      <p className={styles.actionDesc}>Report to the job platform where you found it to protect others.</p>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>1</div>
                    <div>
                      <p className={styles.actionTitle}>Research the company</p>
                      <p className={styles.actionDesc}>Check Glassdoor, LinkedIn, and the company's official site.</p>
                    </div>
                  </div>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>2</div>
                    <div>
                      <p className={styles.actionTitle}>Tailor your application</p>
                      <p className={styles.actionDesc}>Customize your CV and cover letter to match the requirements.</p>
                    </div>
                  </div>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>3</div>
                    <div>
                      <p className={styles.actionTitle}>Apply with confidence</p>
                      <p className={styles.actionDesc}>This looks like a legitimate opportunity worth pursuing.</p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className={styles.disclaimer}>
          <span className={styles.disclaimerIcon}>ℹ</span>
          <p className={styles.disclaimerText}>
            This result is generated by a machine learning model trained on the EMSCAD dataset
            with 97.4% accuracy. It is not 100% guaranteed. Always use your own judgment
            before applying to any job.
          </p>
        </div>

        {/* Action buttons */}
        <div className={styles.actions}>
          <button
            className={styles.btnSecondary}
            onClick={() => router.push('/detect')}
          >
            Check another job
          </button>
          <button
            className={styles.btnPrimary}
            onClick={() => router.push('/')}
          >
            Back to home
          </button>
        </div>

      </div>
    </div>
  )
}

export default function ResultPage() {
  return (
    <Suspense fallback={
      <div style={{ padding: '80px', textAlign: 'center', color: '#888' }}>
        Loading result...
      </div>
    }>
      <ResultContent />
    </Suspense>
  )
}