export type DataState = 'loading' | 'empty' | 'error' | 'ready';
export type ConnectionState = 'connected' | 'disconnected';

interface ResolveDataStateOptions {
  isLoading?: boolean;
  isEmpty?: boolean;
  error?: string | null;
}

export function resolveDataState({
  isLoading = false,
  isEmpty = false,
  error = null,
}: ResolveDataStateOptions): DataState {
  if (error) return 'error';
  if (isLoading) return 'loading';
  if (isEmpty) return 'empty';
  return 'ready';
}

export function resolveConnectionState(connected: boolean): ConnectionState {
  return connected ? 'connected' : 'disconnected';
}

export function getConnectionLabel(state: ConnectionState): string {
  return state === 'connected' ? 'Connected' : 'Disconnected';
}
