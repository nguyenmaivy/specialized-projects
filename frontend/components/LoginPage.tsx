"use client";

import { useState, FormEvent } from 'react';
import { useAuth } from '@/lib/auth-context';
import { signup } from '@/lib/auth-api';
import { Lock, User, Eye, EyeOff, AlertCircle, BarChart3, Mail, ArrowLeft, CheckCircle2, Loader2 } from 'lucide-react';

type AuthMode = 'login' | 'signup' | 'forgot_password';

export default function LoginPage() {
    const { login, error: authError, isLoading: authLoading } = useAuth();
    
    // UI State
    const [mode, setMode] = useState<AuthMode>('login');
    const [isLoading, setIsLoading] = useState(false);
    const [localError, setLocalError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Form Data
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const switchMode = (newMode: AuthMode) => {
        setMode(newMode);
        setLocalError('');
        setSuccessMessage('');
        setUsername('');
        setPassword('');
        setConfirmPassword('');
    };

    const handleLogin = async (e: FormEvent) => {
        e.preventDefault();
        setLocalError('');

        if (!username.trim() || !password) {
            setLocalError('Please enter both username and password.');
            return;
        }

        try {
            await login(username, password);
        } catch {
            // Error is handled by auth context
        }
    };

    const handleSignup = async (e: FormEvent) => {
        e.preventDefault();
        setLocalError('');
        setSuccessMessage('');

        if (!username.trim() || !password || !confirmPassword) {
            setLocalError('Please fill in all fields.');
            return;
        }

        if (password.length < 6) {
            setLocalError('Password must be at least 6 characters.');
            return;
        }

        if (password !== confirmPassword) {
            setLocalError('Passwords do not match.');
            return;
        }

        setIsLoading(true);
        try {
            await signup({ username, password, role: 'viewer' }); // role is ignored on backend anyway
            setSuccessMessage('Account created successfully! You can now log in.');
            setTimeout(() => {
                switchMode('login');
            }, 2000);
        } catch (err: any) {
            setLocalError(err.response?.data?.detail || 'Failed to create account.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleForgotPassword = (e: FormEvent) => {
        e.preventDefault();
        setLocalError('');
        setSuccessMessage('');

        if (!username.trim()) {
            setLocalError('Please enter your username or email.');
            return;
        }

        // Mocking a reset email flow
        setIsLoading(true);
        setTimeout(() => {
            setSuccessMessage(`If an account exists for ${username}, an email with reset instructions has been sent. For local testing, please contact the administrator.`);
            setIsLoading(false);
        }, 1500);
    };

    const error = localError || (mode === 'login' ? authError : '');
    const isWorking = isLoading || authLoading;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
            </div>

            <div className="relative w-full max-w-md">
                {/* Logo & Title */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600 shadow-lg shadow-indigo-500/30 mb-4 transition-transform hover:scale-105">
                        <BarChart3 className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-white">Sales Forecasting Dashboard</h1>
                    <p className="text-slate-400 mt-1">
                        {mode === 'login' && 'Sign in to access your dashboard'}
                        {mode === 'signup' && 'Create a new account'}
                        {mode === 'forgot_password' && 'Reset your password'}
                    </p>
                </div>

                {/* Main Card */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-hidden transition-all duration-300">
                    
                    {/* Status Messages */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 mb-5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm animate-in fade-in">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}
                    
                    {successMessage && (
                        <div className="flex items-start gap-2 p-3 mb-5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm animate-in fade-in">
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                            <span className="leading-tight">{successMessage}</span>
                        </div>
                    )}

                    {/* LOGIN MODE */}
                    {mode === 'login' && (
                        <form onSubmit={handleLogin} className="space-y-5 animate-in slide-in-from-left-4 fade-in">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">Username</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        placeholder="Enter your username"
                                        className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        disabled={isWorking}
                                        autoComplete="username"
                                    />
                                </div>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-1.5">
                                    <label className="block text-sm font-medium text-slate-300">Password</label>
                                    <button 
                                        type="button" 
                                        onClick={() => switchMode('forgot_password')}
                                        className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                                    >
                                        Forgot password?
                                    </button>
                                </div>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Enter your password"
                                        className="w-full pl-11 pr-12 py-3 rounded-xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        disabled={isWorking}
                                        autoComplete="current-password"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300"
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isWorking}
                                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-lg flex justify-center items-center disabled:opacity-50"
                            >
                                {isWorking ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Sign In'}
                            </button>

                            <div className="mt-6 text-center text-sm text-slate-400 pb-2">
                                Don&apos;t have an account?{' '}
                                <button type="button" onClick={() => switchMode('signup')} className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                                    Sign up
                                </button>
                            </div>

                            <div className="pt-4 border-t border-white/5 text-center">
                                <p className="text-xs text-slate-500">
                                    Default: <span className="text-slate-400 font-mono">admin</span> / <span className="text-slate-400 font-mono">admin123</span>
                                </p>
                            </div>
                        </form>
                    )}

                    {/* SIGNUP MODE */}
                    {mode === 'signup' && (
                        <form onSubmit={handleSignup} className="space-y-4 animate-in slide-in-from-right-4 fade-in">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">Username</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        placeholder="Choose a username"
                                        className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        disabled={isWorking}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Min 6 characters"
                                        className="w-full pl-11 pr-12 py-3 rounded-xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        disabled={isWorking}
                                    />
                                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300">
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">Confirm Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type={showConfirmPassword ? 'text' : 'password'}
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        placeholder="Repeat password"
                                        className="w-full pl-11 pr-12 py-3 rounded-xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        disabled={isWorking}
                                    />
                                    <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300">
                                        {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isWorking}
                                className="w-full py-3 mt-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-lg flex justify-center items-center disabled:opacity-50"
                            >
                                {isWorking ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Account'}
                            </button>

                            <div className="mt-6 pt-2 text-center">
                                <button type="button" onClick={() => switchMode('login')} className="text-sm text-slate-400 hover:text-white transition-colors flex items-center justify-center gap-1 mx-auto">
                                    <ArrowLeft className="w-4 h-4" /> Back to login
                                </button>
                            </div>
                        </form>
                    )}

                    {/* FORGOT PASSWORD MODE */}
                    {mode === 'forgot_password' && (
                        <form onSubmit={handleForgotPassword} className="space-y-5 animate-in slide-in-from-right-4 fade-in">
                            <ul className="text-sm text-slate-400 mb-6 space-y-2 list-disc pl-5">
                                <li>Enter the username associated with your account.</li>
                                <li>We will send a password reset link to your registered email address.</li>
                            </ul>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">Username or Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        placeholder="Enter username"
                                        className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        disabled={isWorking || !!successMessage}
                                    />
                                </div>
                            </div>

                            {!successMessage && (
                                <button
                                    type="submit"
                                    disabled={isWorking}
                                    className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-lg flex justify-center items-center disabled:opacity-50"
                                >
                                    {isWorking ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Send Reset Link'}
                                </button>
                            )}

                            <div className="mt-6 pt-2 text-center">
                                <button type="button" onClick={() => switchMode('login')} className="text-sm text-slate-400 hover:text-white transition-colors flex items-center justify-center gap-1 mx-auto">
                                    <ArrowLeft className="w-4 h-4" /> Back to login
                                </button>
                            </div>
                        </form>
                    )}

                </div>
            </div>
        </div>
    );
}
