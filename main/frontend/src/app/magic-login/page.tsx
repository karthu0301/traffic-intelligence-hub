'use client';
import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function MagicLoginPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      router.push('/login');
      return;
    }

    const verify = async () => {
      try {
        const res = await fetch('http://localhost:8000/verify-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token })
        });

        if (!res.ok) {
          throw new Error('Invalid token');
        }

        const data = await res.json();
        localStorage.setItem('token', token);
        localStorage.setItem('userEmail', data.email); // optional
        router.push('/');
      } catch (err) {
        console.error(err);
        setStatus('error');
        router.push('/login');
      }
    };

    verify();
  }, []);

  return (
    <main className="flex items-center justify-center min-h-screen text-white bg-[#213448]">
      {status === 'loading' ? (
        <p>Verifying login token...</p>
      ) : (
        <p>Login failed. Redirecting...</p>
      )}
    </main>
  );
}
