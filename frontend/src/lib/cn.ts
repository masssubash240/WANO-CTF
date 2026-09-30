import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge conditional class names without Tailwind specificity clashes. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
