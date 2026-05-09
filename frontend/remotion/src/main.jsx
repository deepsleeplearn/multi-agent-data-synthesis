import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Player} from '@remotion/player';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
} from 'remotion';

const fps = 30;
const activeDurationSeconds = 60 * 60 * 12;
const durationInFrames = fps * activeDurationSeconds;
const compositionWidth = 1920;
const compositionHeight = 1080;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const fade = (frame, start, end) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const slide = (frame, start, end, from, to) =>
  interpolate(frame, [start, end], [from, to], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const wave = (frame, speed, offset = 0) => Math.sin(frame * speed + offset);

const baseFont =
  '"SFMono-Regular", "JetBrains Mono", "Fira Code", Consolas, monospace';

const styles = {
  fill: {
    background:
      'radial-gradient(circle at 16% 18%, rgba(103, 232, 249, 0.24), transparent 30%), radial-gradient(circle at 78% 22%, rgba(45, 212, 191, 0.24), transparent 34%), linear-gradient(135deg, #101417 0%, #1f2926 47%, #2f2519 100%)',
    color: '#f8fafc',
    fontFamily: baseFont,
    overflow: 'hidden',
  },
  grid: {
    position: 'absolute',
    inset: '-14%',
    backgroundImage:
      'linear-gradient(rgba(255,255,255,0.075) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.075) 1px, transparent 1px)',
    backgroundSize: '64px 64px',
    transformOrigin: '50% 65%',
  },
  particleLayer: {
    position: 'absolute',
    inset: 0,
    overflow: 'hidden',
  },
  particle: {
    position: 'absolute',
    borderRadius: '50%',
    background: '#67e8f9',
    boxShadow: '0 0 18px rgba(103, 232, 249, 0.72)',
  },
  particleBeam: {
    position: 'absolute',
    height: 1,
    transformOrigin: '0 50%',
    background:
      'linear-gradient(90deg, rgba(103,232,249,0), rgba(103,232,249,0.44), rgba(45,212,191,0))',
  },
  zoomLayer: {
    position: 'absolute',
    inset: 0,
    transformOrigin: '50% 50%',
  },
  orbit: {
    position: 'absolute',
    border: '1px solid rgba(148, 163, 184, 0.34)',
    borderRadius: '50%',
    boxShadow:
      'inset 0 0 72px rgba(45,212,191,0.14), 0 0 96px rgba(14,165,233,0.1)',
  },
};

const particles = Array.from({length: 58}, (_, index) => {
  const row = index % 11;
  const column = Math.floor(index / 11);
  const x = 72 + ((index * 137) % 1710);
  const y = 86 + ((index * 191) % 860);
  const size = 3 + ((index * 7) % 9);
  const driftX = (row - 5) * 10 + (column % 2 === 0 ? 34 : -28);
  const driftY = (column - 2) * 14 + (row % 2 === 0 ? -18 : 20);
  const delay = 12 + ((index * 5) % 72);
  const color = index % 3 === 0 ? '#5eead4' : index % 3 === 1 ? '#67e8f9' : '#bae6fd';

  return {index, x, y, size, driftX, driftY, delay, color};
});

const beams = [
  {x: 260, y: 240, width: 420, rotate: -18, delay: 26},
  {x: 1060, y: 196, width: 520, rotate: 11, delay: 42},
  {x: 760, y: 715, width: 470, rotate: -9, delay: 54},
  {x: 1320, y: 625, width: 360, rotate: 22, delay: 70},
];

const useBrowserZoomScale = () => {
  const [zoomScale, setZoomScale] = useState(1);

  useEffect(() => {
    const baseDpr = window.devicePixelRatio || 1;

    const syncScale = () => {
      const currentDpr = window.devicePixelRatio || baseDpr;
      setZoomScale(clamp(currentDpr / baseDpr, 0.72, 1.55));
    };

    syncScale();
    window.addEventListener('resize', syncScale);
    window.visualViewport?.addEventListener('resize', syncScale);
    const timer = window.setInterval(syncScale, 250);

    return () => {
      window.removeEventListener('resize', syncScale);
      window.visualViewport?.removeEventListener('resize', syncScale);
      window.clearInterval(timer);
    };
  }, []);

  return zoomScale;
};

const LoginIntro = ({reducedMotion = false}) => {
  const rawFrame = useCurrentFrame();
  const [liveFrame, setLiveFrame] = useState(rawFrame);
  const zoomScale = useBrowserZoomScale();

  useEffect(() => {
    const startedAt = performance.now() - (rawFrame / fps) * 1000;
    let rafId = 0;

    const tick = () => {
      const elapsed = performance.now() - startedAt;
      setLiveFrame(Math.floor((elapsed / 1000) * fps));
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, []);

  const motionFrame = reducedMotion ? Math.floor(liveFrame / 3) : liveFrame;
  const entryFrame = Math.min(liveFrame, 120);

  const gridX = slide(motionFrame, 0, durationInFrames - 1, -52, 52);
  const orbitProgress = spring({
    frame: entryFrame,
    fps,
    config: {damping: 22, stiffness: 70},
  });

  return (
    <AbsoluteFill style={styles.fill}>
      <div style={{...styles.zoomLayer, transform: `scale(${zoomScale})`}}>
        <div
          style={{
            ...styles.grid,
            opacity: 0.42,
            transform: `perspective(900px) rotateX(58deg) translate(${gridX}px, 20px)`,
          }}
        />
        <div style={styles.particleLayer}>
          {beams.map((beam) => {
            const opacity = fade(entryFrame, beam.delay, beam.delay + 36) * 0.72;
            const pulse = 0.76 + wave(motionFrame, 0.028, beam.delay) * 0.18;
            const width =
              slide(entryFrame, beam.delay, beam.delay + 46, beam.width * 0.18, beam.width) *
              pulse;

            return (
              <div
                key={`${beam.x}-${beam.y}`}
                style={{
                  ...styles.particleBeam,
                  left: beam.x,
                  top: beam.y + wave(motionFrame, 0.018, beam.x) * 16,
                  width,
                  opacity: opacity * (0.82 + wave(motionFrame, 0.04, beam.y) * 0.16),
                  transform: `rotate(${beam.rotate + wave(motionFrame, 0.016, beam.delay) * 3}deg)`,
                }}
              />
            );
          })}
          {particles.map((particle) => {
            const start = particle.delay;
            const opacity = fade(entryFrame, start, start + 28) * 0.88;
            const baseScale = slide(entryFrame, start, start + 34, 0.34, 1);
            const scale = baseScale * (0.92 + wave(motionFrame, 0.045, particle.index) * 0.18);
            const settledX = slide(entryFrame, start, start + 86, particle.x - particle.driftX, particle.x);
            const settledY = slide(entryFrame, start, start + 86, particle.y - particle.driftY, particle.y);
            const x = settledX + wave(motionFrame, 0.021 + particle.index * 0.0002, particle.y) * (18 + particle.size);
            const y = settledY + wave(motionFrame, 0.026 + particle.index * 0.0003, particle.x) * (14 + particle.size * 0.8);

            return (
              <div
                key={particle.index}
                style={{
                  ...styles.particle,
                  left: x,
                  top: y,
                  width: particle.size,
                  height: particle.size,
                  background: particle.color,
                  opacity,
                  transform: `scale(${scale})`,
                }}
              />
            );
          })}
        </div>
        <div
          style={{
            ...styles.orbit,
            width: 720,
            height: 720,
            left: -210,
            top: -165,
            opacity: 0.58,
            transform: `scale(${0.82 + orbitProgress * 0.22}) rotate(${slide(entryFrame, 0, 150, -22, 18)}deg)`,
          }}
        />
        <div
          style={{
            ...styles.orbit,
            width: 560,
            height: 560,
            right: -150,
            bottom: -190,
            opacity: 0.5,
            transform: `scale(${0.86 + orbitProgress * 0.18}) rotate(${slide(entryFrame, 0, 150, 18, -18)}deg)`,
          }}
        />
      </div>

    </AbsoluteFill>
  );
};

const mount = document.getElementById('auth-remotion-root');

if (mount) {
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

  createRoot(mount).render(
    <Player
      component={LoginIntro}
      durationInFrames={durationInFrames}
      compositionWidth={compositionWidth}
      compositionHeight={compositionHeight}
      fps={fps}
      autoPlay
      loop
      controls={false}
      moveToBeginningWhenEnded={false}
      inputProps={{reducedMotion}}
      acknowledgeRemotionLicense
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: 'max(100vw, 177.78vh)',
        height: 'max(100vh, 56.25vw)',
        transform: 'translate(-50%, -50%)',
      }}
    />,
  );
}
