import React, { useState } from 'react'
import './index.css'
import { tailorResume, previewResume } from './api'

export default function App() {
    const [jd, setJd] = useState<File | null>(null)
    const [resume, setResume] = useState<File | null>(null)
    const [busy, setBusy] = useState(false)
    const [baseUrl, setBaseUrl] = useState('http://localhost:8000')
    const [status, setStatus] = useState('')
    const [preview, setPreview] = useState<any | null>(null)

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!jd || !resume) { alert('Please attach both files.'); return; }
        try {
            setBusy(true)
            setStatus('Uploading and tailoring…')
            const blob = await tailorResume(baseUrl, jd, resume)
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = 'tailored_resume.pdf'
            a.click()
            URL.revokeObjectURL(url)
            setStatus('Done! Your tailored PDF has been downloaded.')
        } catch (err: any) {
            setStatus(err?.message || 'Something went wrong')
        } finally {
            setBusy(false)
        }
    }

    const onPreview = async () => {
        if (!jd || !resume) { alert('Please attach both files.'); return; }
        try {
            setBusy(true)
            setStatus('Generating preview…')
            const data = await previewResume(baseUrl, jd, resume)
            setPreview(data)
            setStatus('Preview ready below.')
        } catch (err: any) {
            setStatus(err?.message || 'Preview failed.')
        } finally {
            setBusy(false)
        }
    }

    return (
        <div className="container">
            <h1>ATS Resume Tailor</h1>
            <p>Upload a Job Description and your Resume. We’ll generate a clean, ATS-friendly PDF tailored to that role.</p>

            <form onSubmit={onSubmit}>
                <label>API Base URL</label>
                <input
                    type="text"
                    value={baseUrl}
                    onChange={e => setBaseUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                />

                <label>Job Description (TXT / PDF / DOCX)</label>
                <input type="file" accept=".txt,.pdf,.docx" onChange={e => setJd(e.target.files?.[0] || null)} />

                <label>Resume (TXT / PDF / DOCX)</label>
                <input type="file" accept=".txt,.pdf,.docx" onChange={e => setResume(e.target.files?.[0] || null)} />

                <div style={{ height: 12 }} />

                <div style={{ display: 'flex', gap: 8 }}>
                    <button type="button" disabled={busy} onClick={onPreview}>
                        {busy ? 'Working…' : 'Preview Resume'}
                    </button>
                    <button type="submit" disabled={busy}>
                        {busy ? 'Working…' : 'Download PDF'}
                    </button>
                </div>

                <div className="progress">{status}</div>
            </form>

            {preview && (
                <div className="preview-box">
                    <h2>{preview.name}</h2>
                    <p><em>{preview.contact}</em></p>

                    <h3>Summary</h3>
                    <ul>{(preview.summary || []).map((s: string, i: number) => <li key={i}>{s}</li>)}</ul>

                    <h3>Skills</h3>
                    <p>{(preview.skills || []).join(', ')}</p>

                    <h3>Experience</h3>
                    {(preview.experience_entries || []).map((e: any, i: number) => (
                        <div key={i} style={{ marginBottom: 8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <strong>{e.header}</strong>
                                <span>{e.dates}</span>
                            </div>
                            <ul>{(e.bullets || []).map((b: string, j: number) => <li key={j}>{b}</li>)}</ul>
                        </div>
                    ))}

                    <h3>Projects</h3>
                    {(preview.project_entries || []).map((p: any, i: number) => (
                        <div key={i} style={{ marginBottom: 8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <strong>{p.header}</strong>
                                <span>{p.dates}</span>
                            </div>
                            <ul>{(p.bullets || []).map((b: string, j: number) => <li key={j}>{b}</li>)}</ul>
                        </div>
                    ))}

                    <h3>Education</h3>
                    <ul>{(preview.education || []).map((e: string, i: number) => <li key={i}>{e}</li>)}</ul>
                </div>
            )}
        </div>
    )
}
