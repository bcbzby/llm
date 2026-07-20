import { create } from 'zustand';

type Lang = 'zh' | 'en';

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
  toggle: () => void;
}

export const useLangStore = create<LangState>((set) => {
  const stored = (localStorage.getItem('lang') as Lang) || 'zh';
  return {
    lang: stored,
    setLang: (lang: Lang) => {
      localStorage.setItem('lang', lang);
      set({ lang });
    },
    toggle: () => {
      set((state) => {
        const next = state.lang === 'zh' ? 'en' : 'zh';
        localStorage.setItem('lang', next);
        return { lang: next };
      });
    },
  };
});
