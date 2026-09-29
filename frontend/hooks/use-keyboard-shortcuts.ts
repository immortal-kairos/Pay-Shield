import { useEffect } from 'react';

export type ShortcutConfig = {
  key: string;             
  ctrlKey?: boolean;       
  shiftKey?: boolean;      
  altKey?: boolean;        // Added support for Alt/Option
  handler: () => void;
  disabled?: boolean;
  preventDefault?: boolean;
};

export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const activeElement = document.activeElement;
      const isTypingInInput = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA';

      for (const shortcut of shortcuts) {
        if (shortcut.disabled) continue;

        const matchKey = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const matchCtrl = shortcut.ctrlKey ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey;
        const matchShift = shortcut.shiftKey ? event.shiftKey : !event.shiftKey;
        const matchAlt = shortcut.altKey ? event.altKey : !event.altKey; // Evaluate Alt

        if (matchKey && matchCtrl && matchShift && matchAlt) {
          if (isTypingInInput && event.key !== 'Escape' && !shortcut.ctrlKey && !shortcut.altKey) {
            continue;
          }

          if (shortcut.preventDefault) {
            event.preventDefault();
          }
          shortcut.handler();
          return; 
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}