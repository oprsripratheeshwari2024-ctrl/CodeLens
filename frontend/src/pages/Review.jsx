import React, { useState } from 'react'
import { Star } from 'lucide-react'
import api from '../services/api.js'

export default function Review({ user }) {
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [feedback, setFeedback] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    if (rating === 0) {
      setError('Please select a star rating.')
      return
    }
    setError('')
    try {
      await api.submitReview(user.user_id, rating, feedback)
      setSubmitted(true)
    } catch {
      setError('Could not reach the CodeLens backend.')
    }
  }

  if (submitted) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center fade-in">
        <div className="card p-8">
          <p className="text-lg text-white font-semibold mb-1">Thank you for your feedback!</p>
          <p className="text-sm text-gray-500">Your review helps improve CodeLens.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-lg mx-auto fade-in">
      <h1 className="text-xl font-bold text-white mb-6">Rate CodeLens</h1>
      <div className="card p-6">
        <div className="flex gap-1 mb-5 justify-center">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onMouseEnter={() => setHover(n)}
              onMouseLeave={() => setHover(0)}
              onClick={() => setRating(n)}
            >
              <Star
                size={32}
                className={(hover || rating) >= n ? 'text-primary fill-primary' : 'text-gray-700'}
              />
            </button>
          ))}
        </div>
        <label className="text-xs text-gray-400 mb-1 block">Your Feedback</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Write your feedback here..."
          rows={4}
          className="w-full bg-surface2 border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary transition-colors mb-4"
        />
        {error && <p className="text-xs text-danger mb-3">{error}</p>}
        <button onClick={submit} className="btn-primary w-full py-2.5 text-sm">
          Submit Review
        </button>
      </div>
    </div>
  )
}
