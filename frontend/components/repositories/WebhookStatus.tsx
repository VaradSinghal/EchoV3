'use client';

interface WebhookStatusProps {
    isActive: boolean;
    lastDeliveryAt?: string;
    lastDeliveryStatus?: string;
}

export function WebhookStatus({ isActive, lastDeliveryAt, lastDeliveryStatus }: WebhookStatusProps) {
    const statusColor = !isActive
        ? 'bg-gray-500'
        : lastDeliveryStatus === 'success'
            ? 'bg-green-500'
            : lastDeliveryStatus === 'failed'
                ? 'bg-red-500'
                : 'bg-yellow-500';

    return (
        <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${statusColor}`}></span>
            <span className="text-sm text-gray-300">
                {!isActive ? 'Inactive' : lastDeliveryStatus || 'Pending'}
            </span>
            {lastDeliveryAt && (
                <span className="text-xs text-gray-500">
                    • {new Date(lastDeliveryAt).toLocaleString()}
                </span>
            )}
        </div>
    );
}

export default WebhookStatus;
