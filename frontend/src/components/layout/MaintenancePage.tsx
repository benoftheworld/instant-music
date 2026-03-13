interface Props {
  title: string;
  message: string;
}

export default function MaintenancePage({ title, message }: Props) {
  return (
    <div className="min-h-screen bg-dark text-cream-100 flex flex-col items-center justify-center px-4 py-16">
      {/* Icône */}
      <div className="mb-8 text-primary-500">
        <svg xmlns="http://www.w3.org/2000/svg" className="w-20 h-20 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>

      {/* Logo */}
      <p className="text-3xl font-bold mb-8">
        <span className="text-primary-500">Instant</span>Music
      </p>

      {/* Contenu */}
      <div className="max-w-md w-full text-center space-y-4">
        <h1 className="text-2xl font-bold text-primary-400">
          {title || 'Maintenance en cours'}
        </h1>
        <p className="text-cream-300 leading-relaxed">
          {message || 'Le site est temporairement indisponible pour maintenance. Merci de réessayer dans quelques instants.'}
        </p>
      </div>

      {/* Décoration */}
      <div className="mt-12 flex gap-2">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-2 h-2 rounded-full bg-primary-500 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
