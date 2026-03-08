import { api } from './api';

export const userService = {
  async usernameExists(username: string): Promise<boolean> {
    const response = await api.get('/users/exists/', { params: { username } });
    return response.data?.exists || false;
  },

  async emailExists(email: string): Promise<boolean> {
    const response = await api.get('/users/exists/', { params: { email } });
    return response.data?.exists || false;
  },
};

export default userService;
