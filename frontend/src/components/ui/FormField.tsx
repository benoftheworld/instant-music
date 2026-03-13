import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
  labelRight?: ReactNode;
}

const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, error, hint, labelRight, id, className = '', ...props }, ref) => {
    const fieldId = id ?? `field-${label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
      <div>
        <div className="flex justify-between items-center mb-1">
          <label htmlFor={fieldId} className="block text-sm font-medium">
            {label}
          </label>
          {labelRight}
        </div>
        <input
          ref={ref}
          id={fieldId}
          className={`input ${error ? 'border-red-400 focus:ring-red-500 focus:border-red-500' : ''} ${className}`}
          aria-invalid={!!error}
          aria-describedby={error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined}
          {...props}
        />
        {error && (
          <p id={`${fieldId}-error`} className="mt-1 text-sm text-red-600">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${fieldId}-hint`} className="mt-1 text-sm text-gray-500">
            {hint}
          </p>
        )}
      </div>
    );
  },
);

FormField.displayName = 'FormField';

export default FormField;
