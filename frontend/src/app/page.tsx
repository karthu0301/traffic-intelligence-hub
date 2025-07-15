'use client';
import { useState } from 'react';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);

  const uploadFile = async () => {
    const formData = new FormData();
    if (!file) return;
    formData.append('file', file);

    const res = await fetch('http://192.168.50.143:8000/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();
    alert(JSON.stringify(data));
  };

  return (
    <main className="p-4">
      <h1>Traffic Intelligence Hub</h1>
      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button onClick={uploadFile}>Upload Dataset</button>
    </main>
  );
}
