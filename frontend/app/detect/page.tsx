'use client'

import { useState, type ChangeEvent, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import styles from './detect.module.css'

export default function DetectPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    title: '',
    company: '',
    location: '',
    salary: '',
    description: '',
    requirements: '',
    benefits: '',
    email: '',
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
        title: 'Data Entry Clerk — Work From Home',
        company: 'Global Solutions Inc',
        location: 'Remote',
        salary: '$5,000/week',
        description:
          'No experience needed! Earn $5,000 weekly from home processing simple data orders. Flexible hours, immediate start. Must be 18+. No background check required. Send your details to begin today!',
        requirements:
          'No qualifications needed. Must have internet access. Willing to work independently. No experience required whatsoever.',
        benefits:
          'Work from home. Weekly pay. Unlimited earning potential. Be your own boss. No boss looking over your shoulder.',
        email: '',
      })
    } else {
      setForm({
        title: 'Frontend Engineer — React',
        company: 'Stripe',
        location: 'San Francisco, CA',
        salary: '$130,000 – $160,000/year',
        description:
          'We are looking for a Frontend Engineer to join our Payments UI team. You will build and maintain user-facing features used by millions of businesses worldwide. You will collaborate with product, design, and backend engineers.',
        requirements:
          '3+ years of React experience. Strong understanding of TypeScript, CSS, and web performance. Experience with testing frameworks. Bachelor\'s degree in CS or equivalent experience.',
        benefits:
          'Comprehensive health insurance. 401(k) with matching. Equity package. $3,000 annual learning budget. 20 days PTO. Remote-friendly.',
        email: '',
      })
    }
    setError('')
  }

  function clearForm() {
    setForm({
      title: '',
      company: '',
      location: '',
      salary: '',
      description: '',
      requirements: '',
      benefits: '',
      email: '',
    })
    setError('')
  }

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
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        }
      )

      if (!res.ok) throw new Error('API error')

      const data = await res.json()

      const params = new URLSearchParams({
        prediction: data.prediction,
        confidence: String(data.confidence),
        title: form.title,
        company: form.company,
      })

      router.push(`/result?${params.toString()}`)
    } catch (err) {
      setError(
        'Could not reach the detection server. Make sure your backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  const filled =
    Object.values(form).filter((v) => v.trim() !== '').length

  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Page header */}
        <div className={styles.header}>
          <h1 className={styles.title}>Analyze a job posting</h1>
          <p className={styles.subtitle}>
            Fill in the details from the job listing. The more fields
            you fill, the more accurate the result.
          </p>
        </div>

        {/* Quick fill buttons */}
        <div className={styles.quickFill}>
          <span className={styles.quickLabel}>Try an example:</span>
          <button
            type="button"
            className={styles.quickFake}
            onClick={() => fillExample('fake')}
          >
            Load fake job
          </button>
          <button
            type="button"
            className={styles.quickReal}
            onClick={() => fillExample('real')}
          >
            Load real job
          </button>
          {filled > 0 && (
            <button
              type="button"
              className={styles.clearBtn}
              onClick={clearForm}
            >
              Clear all
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGrid}>

            {/* Left column */}
            <div className={styles.col}>

              <div className={styles.field}>
                <label className={styles.label}>
                  Job title <span className={styles.required}>*</span>
                </label>
                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="e.g. Frontend Engineer"
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Company name</label>
                <input
                  type="text"
                  name="company"
                  value={form.company}
                  onChange={handleChange}
                  placeholder="e.g. Stripe"
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Location</label>
                <input
                  type="text"
                  name="location"
                  value={form.location}
                  onChange={handleChange}
                  placeholder="e.g. Remote or New York, NY"
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Salary / compensation</label>
                <input
                  type="text"
                  name="salary"
                  value={form.salary}
                  onChange={handleChange}
                  placeholder="e.g. $80,000/year or $50/hour"
                  className={styles.input}
                />
              </div>
            <div className={styles.field}>
              <label className={styles.label}>Contact email (optional)</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="e.g. hr@company.com"
                  className={styles.input}
                />
            </div>

              {/* Progress indicator */}
              <div className={styles.progressBox}>
                <div className={styles.progressTop}>
                  <span className={styles.progressLabel}>
                    Form completeness
                  </span>
                  <span className={styles.progressNum}>
                    {Math.round((filled / 8) * 100)}%
                  </span>
                </div>
                <div className={styles.progressBg}>
                  <div
                    className={styles.progressBar}
                    style={{ width: `${(filled / 8) * 100}%` }}
                  ></div>
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
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Paste the full job description here..."
                  className={styles.textarea}
                  rows={5}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Requirements</label>
                <textarea
                  name="requirements"
                  value={form.requirements}
                  onChange={handleChange}
                  placeholder="e.g. 3+ years React, TypeScript..."
                  className={styles.textarea}
                  rows={3}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Benefits</label>
                <textarea
                  name="benefits"
                  value={form.benefits}
                  onChange={handleChange}
                  placeholder="e.g. Health insurance, remote work..."
                  className={styles.textarea}
                  rows={3}
                />
              </div>
            </div>
          </div>

          {/* Error message */}
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
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={loading}
            >
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