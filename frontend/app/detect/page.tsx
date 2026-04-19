'use client'

import { useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from 'react'
import { useRouter } from 'next/navigation'
import styles from './detect.module.css'

export default function DetectPage() {
  const router = useRouter()
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState('')
  const [urlInput, setUrlInput]     = useState('')
  const [urlLoading, setUrlLoading] = useState(false)
  const [urlError, setUrlError]     = useState('')
  const [urlSuccess, setUrlSuccess] = useState('')

  const [form, setForm] = useState({
    title:        '',
    company:      '',
    location:     '',
    salary:       '',
    description:  '',
    requirements: '',
    benefits:     '',
    email:        '',
    website:      '',   // NEW — Layer 5 external verification
  })

  function handleChange(
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    setForm({ ...form, [e.target.name]: e.target.value })
    setError('')
  }

  function fillExample(type: 'fake' | 'real') {
    if (type === 'fake') {
      setForm({
        title:        'Data Entry Clerk — Work From Home',
        company:      'Global Solutions Inc',
        location:     'Remote',
        salary:       '$5,000/week',
        description:  'No experience needed! Earn $5,000 weekly from home processing simple data orders. Flexible hours, immediate start. Must be 18+. No background check required. Send your details to begin today!',
        requirements: 'No qualifications needed. Must have internet access. Willing to work independently. No experience required whatsoever.',
        benefits:     'Work from home. Weekly pay. Unlimited earning potential. Be your own boss. No boss looking over your shoulder.',
        email:        'jobs@globalsolutionsinc-hiring.com',
        website:      'www.globalsolutionsinc-hiring.com',
      })
    } else {
      setForm({
        title:        'Frontend Engineer — React',
        company:      'Stripe',
        location:     'San Francisco, CA',
        salary:       '$130,000 – $160,000/year',
        description:  'We are looking for a Frontend Engineer to join our Payments UI team. You will build and maintain user-facing features used by millions of businesses worldwide. You will collaborate with product, design, and backend engineers.',
        requirements: '3+ years of React experience. Strong understanding of TypeScript, CSS, and web performance. Experience with testing frameworks. Bachelor\'s degree in CS or equivalent experience.',
        benefits:     'Comprehensive health insurance. 401(k) with matching. Equity package. $3,000 annual learning budget. 20 days PTO. Remote-friendly.',
        email:        'careers@stripe.com',
        website:      'https://stripe.com/jobs',
      })
    }
    setError('')
    setUrlSuccess('')
  }

  function clearForm() {
    setForm({
      title: '', company: '', location: '', salary: '',
      description: '', requirements: '', benefits: '',
      email: '', website: '',
    })
    setError('')
    setUrlInput('')
    setUrlError('')
    setUrlSuccess('')
  }

  // ── URL Scanner ──────────────────────────────────
  async function handleUrlScan() {
    const trimmed = urlInput.trim()
    if (!trimmed) return

    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      setUrlError('Please enter a valid URL starting with http:// or https://')
      return
    }

    setUrlLoading(true)
    setUrlError('')
    setUrlSuccess('')
    setError('')

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/scan-url`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ url: trimmed }),
        }
      )

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to scan URL')
      }

      // Auto-fill form with scraped data + use scanned URL as website
      setForm({
        title:        data.title        || '',
        company:      data.company      || '',
        location:     '',
        salary:       '',
        description:  data.description  || '',
        requirements: data.requirements || '',
        benefits:     data.benefits     || '',
        email:        '',
        website:      trimmed,   // use the scanned URL as website field
      })

      setUrlSuccess(
        `Scanned successfully — ${data.title || 'job'} at ${data.company || 'unknown company'}. Form auto-filled below.`
      )

      const params = new URLSearchParams({
        prediction:  data.prediction,
        confidence:  String(data.confidence),
        trust_score: String(data.trust_score),
        risk_level:  data.risk_level,
        flags:       JSON.stringify(data.flags),
        title:       data.title   || 'Unknown Position',
        company:     data.company || 'Unknown Company',
      })

      setTimeout(() => {
        router.push(`/result?${params.toString()}`)
      }, 1200)

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong'
      setUrlError(msg)
    } finally {
      setUrlLoading(false)
    }
  }

  function handleUrlKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleUrlScan()
    }
  }

  // ── Form submit ──────────────────────────────────
  async function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!form.title.trim() || !form.description.trim()) {
      setError('Job title and description are required.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/predict`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(form),   // website field included automatically
        }
      )

      if (!res.ok) throw new Error('API error')

      const data = await res.json()

      // Build verification summary for result page
      const verif = data.verification || {}
      const verifSummary = {
        website_exists:   verif.website_dns?.exists     ?? null,
        website_verdict:  verif.website_content?.verdict ?? null,
        email_exists:     verif.email_domain?.exists    ?? null,
        company_found:    verif.web_presence?.found     ?? null,
        website_reason:   verif.website_content?.reason ?? '',
      }

      const params = new URLSearchParams({
        prediction:  data.prediction,
        confidence:  String(data.confidence),
        trust_score: String(data.trust_score  ?? 50),
        risk_level:  data.risk_level           ?? 'medium',
        flags:       JSON.stringify(data.flags ?? []),
        title:       form.title,
        company:     form.company,
        website:     form.website || '',
        verification: JSON.stringify(verifSummary),
      })

      router.push(`/result?${params.toString()}`)
    } catch {
      setError(
        'Could not reach the detection server. Make sure your backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  // count filled fields including new website field
  const TOTAL_FIELDS = 9
  const filled = Object.values(form).filter((v) => v.trim() !== '').length

  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Page header */}
        <div className={styles.header}>
          <h1 className={styles.title}>Analyze a job posting</h1>
          <p className={styles.subtitle}>
            Paste a job URL to auto-scan it, or fill in the details manually.
            The more fields you fill, the more accurate the result.
          </p>
        </div>

        {/* ── URL Scanner box ── */}
        <div className={styles.urlSection}>
          <div className={styles.urlHeader}>
            <div className={styles.urlTitleRow}>
              <div className={styles.urlIconBox}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M6 10.5L9.5 7 6 3.5" stroke="currentColor" strokeWidth="1.4"
                    strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 8h10" stroke="currentColor" strokeWidth="1.4"
                    strokeLinecap="round"/>
                </svg>
              </div>
              <div>
                <p className={styles.urlTitle}>Scan a job URL</p>
                <p className={styles.urlSubtitle}>
                  Paste any job link — Indeed, Glassdoor, company career pages.
                  We fetch, read, and analyze it automatically.
                </p>
              </div>
            </div>
          </div>

          <div className={styles.urlRow}>
            <input
              type="url"
              value={urlInput}
              onChange={e => { setUrlInput(e.target.value); setUrlError('') }}
              onKeyDown={handleUrlKeyDown}
              placeholder="https://careers.company.com/jobs/engineer-123"
              className={styles.urlInput}
              disabled={urlLoading}
            />
            <button
              type="button"
              className={styles.urlBtn}
              onClick={handleUrlScan}
              disabled={urlLoading || !urlInput.trim()}
            >
              {urlLoading ? (
                <span className={styles.spinnerRow}>
                  <span className={styles.spinnerDark}></span>
                  Scanning...
                </span>
              ) : (
                'Scan URL'
              )}
            </button>
          </div>

          {urlError && (
            <div className={styles.urlErrorBox}>
              <span className={styles.urlErrorIcon}>!</span>
              {urlError}
            </div>
          )}

          {urlSuccess && (
            <div className={styles.urlSuccessBox}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
                style={{flexShrink:0, marginTop:1}}>
                <path d="M2.5 7.5l3 3 6-6" stroke="#3B6D11"
                  strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              {urlSuccess} Redirecting to results...
            </div>
          )}

          <p className={styles.urlNote}>
            LinkedIn not supported (they block automated access). Use manual
            paste for LinkedIn jobs.
          </p>
        </div>

        {/* Divider */}
        <div className={styles.divider}>
          <span className={styles.dividerText}>or fill in manually</span>
        </div>

        {/* Quick fill buttons */}
        <div className={styles.quickFill}>
          <span className={styles.quickLabel}>Try an example:</span>
          <button type="button" className={styles.quickFake}
            onClick={() => fillExample('fake')}>
            Load fake job
          </button>
          <button type="button" className={styles.quickReal}
            onClick={() => fillExample('real')}>
            Load real job
          </button>
          {filled > 0 && (
            <button type="button" className={styles.clearBtn}
              onClick={clearForm}>
              Clear all
            </button>
          )}
        </div>

        {/* Manual form */}
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGrid}>

            {/* Left column */}
            <div className={styles.col}>
              <div className={styles.field}>
                <label className={styles.label}>
                  Job title <span className={styles.required}>*</span>
                </label>
                <input type="text" name="title" value={form.title}
                  onChange={handleChange}
                  placeholder="e.g. Frontend Engineer"
                  className={styles.input} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Company name</label>
                <input type="text" name="company" value={form.company}
                  onChange={handleChange}
                  placeholder="e.g. Stripe"
                  className={styles.input} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Location</label>
                <input type="text" name="location" value={form.location}
                  onChange={handleChange}
                  placeholder="e.g. Remote or New York, NY"
                  className={styles.input} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Salary / compensation</label>
                <input type="text" name="salary" value={form.salary}
                  onChange={handleChange}
                  placeholder="e.g. $80,000/year or $50/hour"
                  className={styles.input} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Contact email</label>
                <input type="email" name="email" value={form.email}
                  onChange={handleChange}
                  placeholder="e.g. hr@company.com"
                  className={styles.input} />
                <p className={styles.fieldHint}>
                  Checks if the email domain actually exists
                </p>
              </div>

              {/* NEW — Company website field */}
              <div className={styles.field}>
                <label className={styles.label}>
                  Company website
                  <span className={styles.newBadge}>NEW</span>
                </label>
                <input type="text" name="website" value={form.website}
                  onChange={handleChange}
                  placeholder="e.g. https://stripe.com/jobs"
                  className={styles.input} />
                <p className={styles.fieldHint}>
                  We verify the site exists and use AI to check if it's a real company
                </p>
              </div>

              {/* Progress */}
              <div className={styles.progressBox}>
                <div className={styles.progressTop}>
                  <span className={styles.progressLabel}>Form completeness</span>
                  <span className={styles.progressNum}>
                    {Math.round((filled / TOTAL_FIELDS) * 100)}%
                  </span>
                </div>
                <div className={styles.progressBg}>
                  <div
                    className={styles.progressBar}
                    style={{ width: `${(filled / TOTAL_FIELDS) * 100}%` }}
                  />
                </div>
                <p className={styles.progressHint}>
                  More fields = more accurate detection
                </p>
              </div>
            </div>

            {/* Right column */}
            <div className={styles.col}>
              <div className={styles.field}>
                <label className={styles.label}>
                  Job description <span className={styles.required}>*</span>
                </label>
                <textarea name="description" value={form.description}
                  onChange={handleChange}
                  placeholder="Paste the full job description here..."
                  className={styles.textarea} rows={5} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Requirements</label>
                <textarea name="requirements" value={form.requirements}
                  onChange={handleChange}
                  placeholder="e.g. 3+ years React, TypeScript..."
                  className={styles.textarea} rows={3} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Benefits</label>
                <textarea name="benefits" value={form.benefits}
                  onChange={handleChange}
                  placeholder="e.g. Health insurance, remote work..."
                  className={styles.textarea} rows={3} />
              </div>

              {/* Layer 5 info card */}
              <div className={styles.verifyCard}>
                <div className={styles.verifyCardHeader}>
                  <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                    <circle cx="7.5" cy="7.5" r="6.5" stroke="currentColor" strokeWidth="1.3"/>
                    <path d="M5 7.5l2 2 3.5-3.5" stroke="currentColor"
                      strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>External verification — Layer 5</span>
                </div>
                <p className={styles.verifyCardText}>
                  When you provide a website or email, our system runs live checks:
                </p>
                <ul className={styles.verifyCardList}>
                  <li>
                    <span className={styles.verifyDot} />
                    DNS lookup — does the domain actually exist?
                  </li>
                  <li>
                    <span className={styles.verifyDot} />
                    AI website analysis — Claude reads the site and judges if it's a real company
                  </li>
                  <li>
                    <span className={styles.verifyDot} />
                    Email domain check — does the email server exist?
                  </li>
                  <li>
                    <span className={styles.verifyDot} />
                    Web presence — does the company appear in search results?
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className={styles.errorBox}>
              <span className={styles.errorIcon}>!</span>
              {error}
            </div>
          )}

          {/* Submit */}
          <div className={styles.submitRow}>
            <p className={styles.submitNote}>
              * Required fields. Your data is never stored.
            </p>
            <button type="submit" className={styles.submitBtn}
              disabled={loading}>
              {loading ? (
                <span className={styles.spinnerRow}>
                  <span className={styles.spinner}></span>
                  Analyzing...
                </span>
              ) : (
                'Analyze this job'
              )}
            </button>
          </div>
        </form>

      </div>
    </div>
  )
}