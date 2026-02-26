import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import type { LoginCredentials, RegisterData, AuthResponse } from '@/types';

export const useLogin = (): UseMutationResult<AuthResponse, Error, LoginCredentials> => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
      navigate('/');
    },
  });
};

export const useRegister = (): UseMutationResult<AuthResponse, Error, RegisterData> => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: authService.register,
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
      navigate('/');
    },
  });
};

export const useLogout = () => {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);

  return () => {
    authService.logout();
    logout();
    navigate('/login');
  };
};
