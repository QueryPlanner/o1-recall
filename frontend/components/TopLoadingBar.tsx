import React, { useEffect, useState } from 'react';

interface TopLoadingBarProps {
  active: boolean;
}

// A simple top loading bar similar to Duolingo's lightweight progress indicator.
// It animates towards 90% while active, then completes and fades out when inactive.
const TopLoadingBar: React.FC<TopLoadingBarProps> = ({ active }) => {
  const [width, setWidth] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (active) {
      setVisible(true);
      setWidth(0);
      const start = performance.now();
      let rafId: number;

      const step = (now: number) => {
        const elapsed = now - start;
        // Ease towards ~90% over ~2.5s while active
        const progress = Math.min(0.9, elapsed / 2500);
        setWidth(Math.floor(progress * 100));
        if (active) {
          rafId = requestAnimationFrame(step);
        }
      };

      rafId = requestAnimationFrame(step);
      return () => cancelAnimationFrame(rafId);
    } else if (visible) {
      // Complete to 100% and fade out shortly after
      setWidth(100);
      const t = setTimeout(() => {
        setVisible(false);
        setWidth(0);
      }, 400);
      return () => clearTimeout(t);
    }
  }, [active, visible]);

  if (!visible) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-[3px] bg-gray-200">
      <div
        className="h-[3px] bg-[#58CC02] transition-[width] duration-200 ease-out"
        style={{ width: `${width}%` }}
      />
    </div>
  );
};

export default TopLoadingBar;


