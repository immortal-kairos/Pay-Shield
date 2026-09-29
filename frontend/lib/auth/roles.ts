
export const isMaker = (role: string | undefined): boolean => role === 'MAKER';
export const isChecker = (role: string | undefined): boolean => role === 'CHECKER';
export const isAdmin = (role: string | undefined): boolean => role === 'ADMIN';

export const getDefaultRouteForRole = (role: string | undefined): string => {
  switch (role) {
    case 'MAKER':
      return '/maker';
    case 'CHECKER':
      return '/checker';
    case 'ADMIN':
      return '/admin';
    default:
      return '/login';
  }
};