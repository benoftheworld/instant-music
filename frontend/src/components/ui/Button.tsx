import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  outline: 'btn-outline',
  ghost: 'btn bg-transparent text-dark hover:bg-cream-200',
  danger: 'btn bg-red-600 text-white hover:bg-red-700 shadow-sm hover:shadow-md',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'text-xs py-1 px-3',
  md: '',
  lg: 'text-lg px-8 py-3',
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading = false, icon, className = '', disabled, children, ...props }, ref) => {
    const classes = [
      variantClasses[variant],
      sizeClasses[size],
      'inline-flex items-center justify-center gap-2',
      (disabled || loading) ? 'opacity-50 cursor-not-allowed' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button ref={ref} className={classes} disabled={disabled || loading} {...props}>
        {loading ? (
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : icon ? (
          <span className="flex-shrink-0">{icon}</span>
        ) : null}
        {children}
      </button>
    );
  },
);

Button.displayName = 'Button';

export default Button;
