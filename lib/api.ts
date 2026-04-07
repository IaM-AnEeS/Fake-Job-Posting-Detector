export type JobForm = {
  title: string
  company: string
  location: string
  salary: string
  description: string
  requirements: string
  benefits: string
}

export type PredictionResult = {
  prediction: 'fake' | 'real'
  confidence: number
}

export async function detectJob(form: JobForm): Promise<PredictionResult> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  })

  if (!res.ok) {
    throw new Error('Prediction failed')
  }

  return res.json()
}