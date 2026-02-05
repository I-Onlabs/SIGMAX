import type { ButtonHTMLAttributes } from 'react';

export default function SecondaryAction({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`px-4 py-2 rounded-[var(--radius)] text-sm border border-[var(--line)] disabled:opacity-50 disabled:cursor-not-allowed ${className || ''}`}
    />
  );
}
