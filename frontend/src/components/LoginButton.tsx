import { useState } from "react";
import { useSWRConfig } from "swr";
import { api, Me } from "../lib/api";

export default function LoginButton({
  me,
  loading,
}: {
  me: Me | undefined;
  loading: boolean;
}) {
  const { mutate } = useSWRConfig();
  const [showDev, setShowDev] = useState(false);
  const [email, setEmail] = useState("");

  if (loading) return <span className="text-ink-400">…</span>;

  if (me) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-ink-700 dark:text-ink-200">{me.name}</span>
        <button
          className="text-ink-500 dark:text-ink-400 hover:text-ink-900 dark:hover:text-ink-100 transition-colors"
          onClick={async () => {
            await api.logout();
            mutate("me");
          }}
        >
          sign out
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <a
        href="/api/auth/google"
        className="bg-accent text-white px-3 py-1.5 rounded text-sm hover:bg-accent-ink glow-accent transition-shadow"
      >
        Sign in
      </a>
      <button
        type="button"
        className="text-ink-500 dark:text-ink-500 hover:text-ink-900 dark:hover:text-ink-300 text-xs transition-colors"
        onClick={() => setShowDev((s) => !s)}
        title="Use only in local dev"
      >
        dev
      </button>
      {showDev && (
        <form
          className="flex items-center gap-1"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!email) return;
            await api.devLogin(email);
            mutate("me");
            setShowDev(false);
            setEmail("");
          }}
        >
          <input
            type="email"
            placeholder="dev@local"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="border border-ink-300 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100 dark:placeholder-ink-400 focus:ring-2 focus:ring-accent/40 focus:outline-none rounded px-2 py-1 text-xs"
            autoFocus
          />
          <button className="text-xs underline text-ink-700 dark:text-ink-300">go</button>
        </form>
      )}
    </div>
  );
}
