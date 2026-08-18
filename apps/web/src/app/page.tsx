export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-8 text-center text-foreground">
      <h1 className="text-5xl font-semibold tracking-tight">Ngabo</h1>
      <p className="max-w-xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
        An open-source, event-driven antimicrobial-resistance surveillance and
        incident-response system.
      </p>
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        Current status: <code className="rounded bg-black/[.06] px-1.5 py-0.5 font-mono text-[0.9em] dark:bg-white/[.08]">v0.1.0</code>{" "}
        hackathon MVP in development.
      </p>
    </main>
  );
}
