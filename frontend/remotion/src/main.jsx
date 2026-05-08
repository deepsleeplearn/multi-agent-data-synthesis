import React from 'react';
import {createRoot} from 'react-dom/client';
import {Player} from '@remotion/player';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const fps = 30;
const durationInFrames = 240;
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
  wordmarkWrap: {
    position: 'absolute',
    left: 150,
    top: 410,
    display: 'flex',
    alignItems: 'center',
    gap: 24,
  },
  wordmark: {
    display: 'flex',
    gap: 12,
  },
  tile: {
    width: 74,
    height: 74,
    border: '1px solid rgba(255,255,255,0.28)',
    borderRadius: 16,
    display: 'grid',
    placeItems: 'center',
    background: 'rgba(15, 23, 42, 0.46)',
    boxShadow: '0 24px 54px rgba(0,0,0,0.26)',
    color: '#67e8f9',
    fontSize: 34,
    fontWeight: 900,
  },
  nameBlock: {
    borderLeft: '2px solid rgba(103,232,249,0.72)',
    paddingLeft: 22,
  },
  platformName: {
    margin: 0,
    color: '#ffffff',
    fontSize: 58,
    fontWeight: 900,
    lineHeight: 1.05,
  },
  fullName: {
    margin: '10px 0 0',
    color: 'rgba(226,232,240,0.7)',
    fontSize: 20,
    lineHeight: 1.25,
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

const LetterTile = ({letter, index, frame}) => {
  const {fps: configFps} = useVideoConfig();
  const scale = spring({
    frame: frame - index * 5,
    fps: configFps,
    config: {damping: 16, stiffness: 115},
  });
  const y = slide(frame, index * 5, 30 + index * 5, 56, 0);

  return (
    <div
      style={{
        ...styles.tile,
        opacity: fade(frame, index * 4, 20 + index * 5),
        transform: `translateY(${y}px) scale(${clamp(scale, 0.72, 1.08)})`,
      }}
    >
      {letter}
    </div>
  );
};

const LoginIntro = ({reducedMotion = false}) => {
  const rawFrame = useCurrentFrame();
  const frame = reducedMotion ? 96 : rawFrame;

  const gridX = slide(frame, 0, durationInFrames - 1, -52, 52);
  const orbitProgress = spring({
    frame,
    fps,
    config: {damping: 22, stiffness: 70},
  });

  return (
    <AbsoluteFill style={styles.fill}>
      <div
        style={{
          ...styles.grid,
          opacity: 0.42,
          transform: `perspective(900px) rotateX(58deg) translate(${gridX}px, 20px)`,
        }}
      />
      <div style={styles.particleLayer}>
        {beams.map((beam) => {
          const opacity = fade(frame, beam.delay, beam.delay + 36) * 0.72;
          const width = slide(frame, beam.delay, beam.delay + 46, beam.width * 0.18, beam.width);

          return (
            <div
              key={`${beam.x}-${beam.y}`}
              style={{
                ...styles.particleBeam,
                left: beam.x,
                top: beam.y,
                width,
                opacity,
                transform: `rotate(${beam.rotate}deg)`,
              }}
            />
          );
        })}
        {particles.map((particle) => {
          const start = particle.delay;
          const opacity = fade(frame, start, start + 28) * 0.88;
          const scale = slide(frame, start, start + 34, 0.34, 1);
          const x = slide(frame, start, durationInFrames - 1, particle.x - particle.driftX, particle.x);
          const y = slide(frame, start, durationInFrames - 1, particle.y - particle.driftY, particle.y);

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
          transform: `scale(${0.82 + orbitProgress * 0.22}) rotate(${slide(frame, 0, 150, -22, 18)}deg)`,
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
          transform: `scale(${0.86 + orbitProgress * 0.18}) rotate(${slide(frame, 0, 150, 18, -18)}deg)`,
        }}
      />

      <div style={styles.wordmarkWrap}>
        <div style={styles.wordmark}>
          {['C', 'A', 'X'].map((letter, index) => (
            <LetterTile key={letter} letter={letter} index={index} frame={frame} />
          ))}
        </div>
        <div
          style={{
            ...styles.nameBlock,
            opacity: fade(frame, 24, 48),
            transform: `translateX(${slide(frame, 24, 50, -18, 0)}px)`,
          }}
        >
          <p style={styles.platformName}>CustAnnoX</p>
          <p style={styles.fullName}>客服标注平台</p>
        </div>
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
      autoPlay={!reducedMotion}
      loop={false}
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
