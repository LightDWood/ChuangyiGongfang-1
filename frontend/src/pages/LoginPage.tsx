import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const login = useAuthStore((state) => state.login);
  const register = useAuthStore((state) => state.register);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      if (isRegister) {
        await register(username, email, password);
        setIsRegister(false);
        setError('注册成功，请登录');
      } else {
        await login(username, password);
        navigate('/chat');
      }
    } catch {
      setError(isRegister ? '注册失败' : '登录失败');
    }
  };

  const inputClass = "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-500";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white p-8 rounded-xl shadow-lg w-96">
        <h1 className="text-2xl font-bold mb-2 text-center text-gray-900">
          需求收敛智能体
        </h1>
        <p className="text-center text-gray-500 mb-6 text-sm">
          智能需求分析与收敛系统
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              placeholder="用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={inputClass}
              required
            />
          </div>
          {isRegister && (
            <div>
              <input
                type="email"
                placeholder="邮箱"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
                required
              />
            </div>
          )}
          <div>
            <input
              type="password"
              placeholder="密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              required
            />
          </div>
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            {isRegister ? '注册' : '登录'}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-gray-600">
          {isRegister ? '已有账号?' : '没有账号?'}{' '}
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            {isRegister ? '登录' : '注册'}
          </button>
        </p>
      </div>
    </div>
  );
}
