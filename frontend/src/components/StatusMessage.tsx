interface StatusMessageProps {
  tone?: 'info' | 'error' | 'empty';
  title: string;
  description?: string;
}

const toneClassMap: Record<NonNullable<StatusMessageProps['tone']>, string> = {
  info: 'status-message--info',
  error: 'status-message--error',
  empty: 'status-message--empty',
};

const StatusMessage = ({ tone = 'info', title, description }: StatusMessageProps) => {
  const toneClass = toneClassMap[tone] ?? toneClassMap.info;
  return (
    <div className={`status-message ${toneClass}`}>
      <h4>{title}</h4>
      {description && <p>{description}</p>}
    </div>
  );
};

export default StatusMessage;
