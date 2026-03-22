import { useAuthStore } from '../../stores';

export default function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="h-14 border-b bg-white flex items-center justify-between px-4">
      <h1 className="text-lg font-semibold">需求收敛智能体</h1>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{user?.username}</span>
        <button
          onClick={logout}
          className="text-sm text-red-500 hover:text-red-600"
        >
          退出
        </button>
      </div>
    </header>
  );
}
