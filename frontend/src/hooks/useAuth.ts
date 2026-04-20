'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, login, logout, register, loadUser } = useAuthStore();

  useEffect(() => {
    if (!user && isAuthenticated) {
      loadUser();
    }
  }, [user, isAuthenticated, loadUser]);

  useEffect(() => {
    if (requireAuth && !isAuthenticated && !isLoading) {
      router.push('/auth/login');
    }
  }, [requireAuth, isAuthenticated, isLoading, router]);

  return { user, isAuthenticated, isLoading, login, logout, register };
}
