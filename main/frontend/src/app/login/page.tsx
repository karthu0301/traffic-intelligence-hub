'use client';
import { useAuth } from '../hooks/useAuth';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) router.push('/');
  }, [isAuthenticated]);

  const handleSendMagicLink = async () => {
    const res = await fetch('http://localhost:8000/send-magic-link', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    if (res.ok) {
      setSent(true);
    } else {
      alert('Failed to send login link. Please try again.');
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-[#213448] text-white font-sans">
      <h1 className="text-3xl font-bold mb-6">Login with Email</h1>

      {!sent ? (
        <div className="flex flex-col space-y-4 w-80">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="p-2 rounded bg-[#94B4C1]"
            placeholder="Enter your email"
          />
          <button
            onClick={handleSendMagicLink}
            className="bg-[#94B4C1] text-[#213448] font-semibold p-2 rounded"
          >
            Send Magic Link
          </button>
        </div>
      ) : (
        <p className="text-green-300">✅ Link sent! Check your email.</p>
      )}
    </main>
  );
}
