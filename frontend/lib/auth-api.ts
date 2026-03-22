import axios from 'axios';

const authApi = axios.create({
    baseURL: 'http://localhost:8000/auth',
});

// Add auth token to every request automatically
authApi.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 responses globally
authApi.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.reload();
        }
        return Promise.reject(error);
    }
);

export const changePassword = async (data: any) => {
    const response = await authApi.put('/change-password', data);
    return response.data;
};

export const getUsers = async () => {
    const response = await authApi.get('/users');
    return response.data;
};

export const signup = async (data: any) => {
    // using axios directly without interceptors to avoid auth headers on signup
    const response = await axios.post('http://localhost:8000/auth/signup', data);
    return response.data;
};

export const deleteUser = async (username: string) => {
    const response = await authApi.delete(`/users/${username}`);
    return response.data;
};
