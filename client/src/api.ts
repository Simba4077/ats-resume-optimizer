export async function tailorResume(baseUrl: string, jd: File, resume: File): Promise<Blob> {
    const form = new FormData();
    form.append('jd', jd);
    form.append('resume', resume);

    const res = await fetch(`${baseUrl}/api/tailor`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    return await res.blob();
}

export async function previewResume(baseUrl: string, jd: File, resume: File) {
    const formData = new FormData();
    formData.append("jd", jd);
    formData.append("resume", resume);

    const res = await fetch(`${baseUrl}/api/preview`, { method: "POST", body: formData });
    if (!res.ok) throw new Error("Preview request failed");
    return res.json();
}

