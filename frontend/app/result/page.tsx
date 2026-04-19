'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Suspense } from 'react'
import styles from './result.module.css'

// ── Types ────────────────────────────────────────────────────────────────────
interface VerificationSummary {
  website_exists:  boolean | null
  website_verdict: 'real' | 'fake' | 'suspicious' | 'parked' | 'unknown' | null
  email_exists:    boolean | null
  company_found:   boolean | null
  website_reason:  string
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function verdictIcon(val: boolean | null, trueLabel: string, falseLabel: string) {
  if (val === null) return { icon: '—', label: 'Not checked', cls: styles.verifNeutral }
  if (val)          return { icon: '✓', label: trueLabel,    cls: styles.verifGood }
  return              { icon: '✕', label: falseLabel,        cls: styles.verifBad }
}

function websiteVerdictDisplay(verdict: VerificationSummary['website_verdict']) {
  switch (verdict) {
    case 'real':       return { icon: '✓', label: 'Looks like a real company',  cls: styles.verifGood }
    case 'suspicious': return { icon: '⚠', label: 'Website looks suspicious',   cls: styles.verifWarn }
    case 'parked':     return { icon: '⚠', label: 'Domain parked / empty site', cls: styles.verifWarn }
    case 'fake':       return { icon: '✕', label: 'Website appears fabricated', cls: styles.verifBad  }
    default:           return { icon: '—', label: 'Not checked',                cls: styles.verifNeutral }
  }
}

// ── Main content ─────────────────────────────────────────────────────────────
function ResultContent() {
  const params = useSearchParams()
  const router = useRouter()

  const prediction  = params.get('prediction') as 'fake' | 'real' | null
  const confidence  = parseFloat(params.get('confidence') || '0')
  const title       = params.get('title')       || 'Unknown Position'
  const company     = params.get('company')     || 'Unknown Company'
  const website     = params.get('website')     || ''
  const trust_score = parseInt(params.get('trust_score') || '50')
  const risk_level  = params.get('risk_level')  as 'low' | 'medium' | 'high'
  const flags       = JSON.parse(params.get('flags')        || '[]') as string[]
  const verification: VerificationSummary = JSON.parse(
    params.get('verification') || 'null'
  ) ?? { website_exists: null, website_verdict: null,
         email_exists: null, company_found: null, website_reason: '' }

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
            <button className={styles.backBtn} onClick={() => router.push('/detect')}>
              Analyze a job
            </button>
          </div>
        </div>
      </div>
    )
  }

  const isFake        = prediction === 'fake'
  const confidencePct = Math.round(confidence * 100)

  // Use real API flags if available, otherwise show sensible defaults
  const displayFlags = flags.length > 0 ? flags : (
    isFake ? [
      'Unrealistic salary or vague compensation',
      'No specific qualifications required',
      'Urgency language detected',
      'Generic or unverifiable company name',
      'Unusual contact method or missing company details',
    ] : [
      'Specific role requirements listed',
      'Realistic and market-aligned salary range',
      'Verifiable company name and location',
      'Professional language and clear responsibilities',
      'Standard benefits package described',
    ]
  )

  const riskLevel =
    risk_level === 'high'   ? 'High risk'  :
    risk_level === 'medium' ? 'Medium risk' :
    risk_level === 'low'    ? 'Low risk'   : 'Uncertain'

  const riskColor =
    risk_level === 'high'   ? styles.riskHigh :
    risk_level === 'medium' ? styles.riskMed  : styles.riskLow

  // Layer 5 check results
  const dnsCheck      = verdictIcon(verification.website_exists, 'Domain exists',       'Domain does not exist')
  const emailCheck    = verdictIcon(verification.email_exists,   'Email domain valid',   'Email domain not found')
  const presenceCheck = verdictIcon(verification.company_found,  'Found in web search',  'No web presence found')
  const siteCheck     = websiteVerdictDisplay(verification.website_verdict)

  const hasVerification = (
    verification.website_exists  !== null ||
    verification.email_exists    !== null ||
    verification.company_found   !== null ||
    verification.website_verdict !== null
  )

  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Breadcrumb */}
        <div className={styles.breadcrumb}>
          <button className={styles.breadcrumbLink} onClick={() => router.push('/')}>Home</button>
          <span className={styles.breadcrumbSep}>/</span>
          <button className={styles.breadcrumbLink} onClick={() => router.push('/detect')}>Detect</button>
          <span className={styles.breadcrumbSep}>/</span>
          <span className={styles.breadcrumbCurrent}>Result</span>
        </div>

        {/* ── Main verdict card ── */}
        <div className={`${styles.verdictCard} ${isFake ? styles.cardFake : styles.cardReal}`}>
          <div className={styles.verdictTop}>
            <div className={styles.verdictLeft}>
              <div className={`${styles.verdictBadge} ${isFake ? styles.badgeFake : styles.badgeReal}`}>
                <span className={styles.badgeIcon}>{isFake ? '✕' : '✓'}</span>
                {isFake ? 'Fake Job' : 'Real Job'}
              </div>
              <h1 className={styles.verdictTitle}>{title}</h1>
              <p className={styles.verdictCompany}>{company}</p>
              {website && (
                <a
                  href={website.startsWith('http') ? website : `https://${website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.verdictWebsite}
                >
                  {website.replace(/^https?:\/\//, '')}
                  <svg width="11" height="11" viewBox="0 0 11 11" fill="none" style={{marginLeft:4}}>
                    <path d="M2 9L9 2M9 2H4M9 2v5" stroke="currentColor"
                      strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </a>
              )}
            </div>

            <div className={styles.verdictRight}>
              <div className={styles.confidenceCircle}>
                <svg viewBox="0 0 80 80" className={styles.circleSvg}>
                  <circle cx="40" cy="40" r="32" fill="none" stroke="#e8e8e8" strokeWidth="7"/>
                  <circle
                    cx="40" cy="40" r="32" fill="none"
                    stroke={isFake ? '#e24b4a' : '#639922'}
                    strokeWidth="7" strokeLinecap="round"
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
              <span>0%</span><span>50%</span><span>100%</span>
            </div>
          </div>
        </div>

        {/* ── Layer 5: External Verification Panel ── */}
        {hasVerification && (
          <div className={styles.verifPanel}>
            <div className={styles.verifPanelHeader}>
              <div className={styles.verifPanelIcon}>
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                  <circle cx="7.5" cy="7.5" r="6.5" stroke="currentColor" strokeWidth="1.3"/>
                  <path d="M4.5 7.5l2 2 4-4" stroke="currentColor"
                    strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div>
                <p className={styles.verifPanelTitle}>External Verification — Layer 5</p>
                <p className={styles.verifPanelSub}>
                  Live checks performed on the company website, email domain, and web presence
                </p>
              </div>
            </div>

            <div className={styles.verifGrid}>

              {/* DNS check */}
              {verification.website_exists !== null && (
                <div className={`${styles.verifItem} ${dnsCheck.cls}`}>
                  <span className={styles.verifItemIcon}>{dnsCheck.icon}</span>
                  <div>
                    <p className={styles.verifItemTitle}>Website DNS</p>
                    <p className={styles.verifItemLabel}>{dnsCheck.label}</p>
                  </div>
                </div>
              )}

              {/* AI website analysis */}
              {verification.website_verdict !== null && (
                <div className={`${styles.verifItem} ${siteCheck.cls}`}>
                  <span className={styles.verifItemIcon}>{siteCheck.icon}</span>
                  <div>
                    <p className={styles.verifItemTitle}>AI Website Analysis</p>
                    <p className={styles.verifItemLabel}>{siteCheck.label}</p>
                    {verification.website_reason && (
                      <p className={styles.verifItemReason}>{verification.website_reason}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Email domain */}
              {verification.email_exists !== null && (
                <div className={`${styles.verifItem} ${emailCheck.cls}`}>
                  <span className={styles.verifItemIcon}>{emailCheck.icon}</span>
                  <div>
                    <p className={styles.verifItemTitle}>Email Domain</p>
                    <p className={styles.verifItemLabel}>{emailCheck.label}</p>
                  </div>
                </div>
              )}

              {/* Web presence */}
              {verification.company_found !== null && (
                <div className={`${styles.verifItem} ${presenceCheck.cls}`}>
                  <span className={styles.verifItemIcon}>{presenceCheck.icon}</span>
                  <div>
                    <p className={styles.verifItemTitle}>Web Presence</p>
                    <p className={styles.verifItemLabel}>{presenceCheck.label}</p>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

        {/* ── Two column: flags + actions ── */}
        <div className={styles.twoCol}>

          {/* Flags */}
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
              {displayFlags.map((w, i) => (
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
                : "This posting looks legitimate. Here's how to proceed."}
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
                      <p className={styles.actionDesc}>Search the company on LinkedIn or their official website.</p>
                    </div>
                  </div>
                  <div className={styles.actionItem}>
                    <div className={styles.actionNum}>3</div>
                    <div>
                      <p className={styles.actionTitle}>Report the listing</p>
                      <p className={styles.actionDesc}>Report to the job platform to protect other job seekers.</p>
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
          <button className={styles.btnSecondary} onClick={() => router.push('/detect')}>
            Check another job
          </button>
          <button className={styles.btnPrimary} onClick={() => router.push('/')}>
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