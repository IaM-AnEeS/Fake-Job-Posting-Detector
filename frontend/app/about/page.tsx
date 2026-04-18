import styles from './about.module.css'
import Link from 'next/link'

export default function AboutPage() {
  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Header */}
        <div className={styles.header}>
          <div className={styles.badge}>About this project</div>
          <h1 className={styles.title}>How JobGuard works</h1>
          <p className={styles.subtitle}>
            A machine learning system trained on 18,000 real and fake
            job postings to protect job seekers from scams.
          </p>
        </div>

        {/* Mission */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>The problem we're solving</h2>
          <p className={styles.sectionText}>
            Every day thousands of job seekers fall victim to fraudulent
            job postings. These scams steal personal information, charge
            upfront fees, and waste months of a person's time. JobGuard
            uses machine learning to detect these scams instantly — before
            you apply.
          </p>
        </section>

        {/* Stats */}
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <span className={styles.statNum}>18,000+</span>
            <span className={styles.statLabel}>Jobs in training dataset</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statNum}>97.4%</span>
            <span className={styles.statLabel}>Model accuracy</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statNum}>4.8%</span>
            <span className={styles.statLabel}>Fraud rate in dataset</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statNum}>&lt; 1s</span>
            <span className={styles.statLabel}>Detection speed</span>
          </div>
        </div>

        {/* How it works */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>How the ML model works</h2>
          <p className={styles.sectionText}>
            The model uses a two-stage pipeline. First, a TF-IDF vectorizer
            converts the job text into 15,000 numerical features — each one
            representing how important a word or phrase is in that posting.
            Then a Logistic Regression classifier weighs each feature and
            outputs a probability of the job being fake.
          </p>

          <div className={styles.pipeline}>
            <div className={styles.pipeStep}>
              <div className={styles.pipeNum}>1</div>
              <h3 className={styles.pipeTitle}>Text cleaning</h3>
              <p className={styles.pipeDesc}>
                All 7 fields are combined — title, company, location,
                salary, description, requirements, benefits — into one
                text string. HTML tags and special characters are removed.
              </p>
            </div>
            <div className={styles.pipeArrow}>→</div>
            <div className={styles.pipeStep}>
              <div className={styles.pipeNum}>2</div>
              <h3 className={styles.pipeTitle}>TF-IDF vectorizer</h3>
              <p className={styles.pipeDesc}>
                Converts text into 15,000 numbers using unigrams and
                bigrams. Bigrams like "no experience" and "work from home"
                are far more powerful signals than single words alone.
              </p>
            </div>
            <div className={styles.pipeArrow}>→</div>
            <div className={styles.pipeStep}>
              <div className={styles.pipeNum}>3</div>
              <h3 className={styles.pipeTitle}>Logistic Regression</h3>
              <p className={styles.pipeDesc}>
                Trained with class_weight='balanced' to handle the
                imbalanced dataset (only 4.8% fake). Outputs a probability
                score — the confidence percentage you see in the result.
              </p>
            </div>
          </div>
        </section>

        {/* Warning signals */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Signals the model looks for</h2>
          <div className={styles.signalsGrid}>
            <div className={styles.signalCard}>
              <div className={styles.signalHeader}>
                <div className={`${styles.signalDot} ${styles.dotFake}`}></div>
                <h3 className={styles.signalTitle}>Fake job signals</h3>
              </div>
              <ul className={styles.signalList}>
                <li>"No experience required"</li>
                <li>Unrealistically high salary</li>
                <li>"Immediate start", "apply now"</li>
                <li>Vague company descriptions</li>
                <li>"No background check"</li>
                <li>Weekly PayPal payments</li>
                <li>Generic job descriptions</li>
              </ul>
            </div>
            <div className={styles.signalCard}>
              <div className={styles.signalHeader}>
                <div className={`${styles.signalDot} ${styles.dotReal}`}></div>
                <h3 className={styles.signalTitle}>Real job signals</h3>
              </div>
              <ul className={styles.signalList}>
                <li>Specific degree requirements</li>
                <li>Market-aligned salary ranges</li>
                <li>Years of experience specified</li>
                <li>Verifiable company names</li>
                <li>Standard benefits (401k, health)</li>
                <li>Technical skills listed</li>
                <li>Professional language throughout</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Dataset */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>The dataset</h2>
          <p className={styles.sectionText}>
            This project uses the EMSCAD dataset — Employment Scam Aegean
            Dataset — published on Kaggle. It contains 17,880 real-world
            job postings collected between 2012 and 2014, labeled as
            legitimate or fraudulent by human reviewers.
          </p>
          <div className={styles.datasetCard}>
            <div className={styles.datasetRow}>
              <span className={styles.datasetKey}>Dataset name</span>
              <span className={styles.datasetVal}>EMSCAD — Real or Fake Job Postings</span>
            </div>
            <div className={styles.datasetRow}>
              <span className={styles.datasetKey}>Source</span>
              <span className={styles.datasetVal}>Kaggle — shivamb</span>
            </div>
            <div className={styles.datasetRow}>
              <span className={styles.datasetKey}>Total records</span>
              <span className={styles.datasetVal}>17,880 job postings</span>
            </div>
            <div className={styles.datasetRow}>
              <span className={styles.datasetKey}>Fake postings</span>
              <span className={styles.datasetVal}>866 (4.84%)</span>
            </div>
            <div className={styles.datasetRow}>
              <span className={styles.datasetKey}>Real postings</span>
              <span className={styles.datasetVal}>17,014 (95.16%)</span>
            </div>
            <div className={styles.datasetRow}>
              <span className={styles.datasetKey}>Train / test split</span>
              <span className={styles.datasetVal}>80% train, 20% test</span>
            </div>
          </div>
        </section>

        {/* Tech stack */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Tech stack</h2>
          <div className={styles.techGrid}>
            <div className={styles.techCard}>
              <div className={styles.techLayer}>Frontend</div>
              <div className={styles.techItems}>
                <span className={styles.techItem}>Next.js 14</span>
                <span className={styles.techItem}>CSS Modules</span>
                <span className={styles.techItem}>TypeScript</span>
                <span className={styles.techItem}>React Hook Form</span>
              </div>
            </div>
            <div className={styles.techCard}>
              <div className={styles.techLayer}>Backend</div>
              <div className={styles.techItems}>
                <span className={styles.techItem}>FastAPI</span>
                <span className={styles.techItem}>Python 3.11</span>
                <span className={styles.techItem}>Uvicorn</span>
                <span className={styles.techItem}>Pydantic</span>
              </div>
            </div>
            <div className={styles.techCard}>
              <div className={styles.techLayer}>ML / Data</div>
              <div className={styles.techItems}>
                <span className={styles.techItem}>scikit-learn</span>
                <span className={styles.techItem}>pandas</span>
                <span className={styles.techItem}>numpy</span>
                <span className={styles.techItem}>joblib</span>
              </div>
            </div>
            <div className={styles.techCard}>
              <div className={styles.techLayer}>Deployment</div>
              <div className={styles.techItems}>
                <span className={styles.techItem}>Vercel</span>
                <span className={styles.techItem}>Render</span>
                <span className={styles.techItem}>GitHub</span>
                <span className={styles.techItem}>CI/CD</span>
              </div>
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <div className={styles.disclaimer}>
          <h3 className={styles.disclaimerTitle}>Important disclaimer</h3>
          <p className={styles.disclaimerText}>
            JobGuard is an AI-powered tool with 97.4% accuracy on the
            test dataset. It is not 100% guaranteed and should not be
            your only method of verifying a job posting. Always research
            the company independently, never pay upfront fees, and never
            share sensitive personal information before verifying a
            company's legitimacy.
          </p>
        </div>

        {/* CTA */}
        <div className={styles.cta}>
          <h2 className={styles.ctaTitle}>Ready to check a job?</h2>
          <p className={styles.ctaSub}>
            Paste any job listing and get an instant verdict.
          </p>
          <Link href="/detect" className={styles.ctaBtn}>
            Analyze a job posting
          </Link>
        </div>

      </div>
    </div>
  )
}