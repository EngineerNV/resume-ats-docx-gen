interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="relative">
        {/* Outer ring */}
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-600"></div>
        {/* Inner ring */}
        <div 
          className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-400 absolute top-0 left-0" 
          style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}
        ></div>
      </div>
      {message && (
        <p className="mt-4 text-gray-600 dark:text-gray-300 animate-pulse">{message}</p>
      )}
    </div>
  );
}
