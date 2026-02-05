import type { ButtonHTMLAttributes } from 'react';

export default function PrimaryAction({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`px-4 py-2 rounded-[var(--radius)] text-sm bg-[var(--accent)] text-white disabled:opacity-50 disabled:cursor-not-allowed ${className || ''}`}
    />
  );
}
