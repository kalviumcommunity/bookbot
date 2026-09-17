/**
 * WelcomeTransition.jsx
 *
 * Cinematic full-screen welcome overlay shown immediately after a successful
 * login or signup. Plays a ~2.8s entrance → hold → exit animation, then calls
 * onDone() so the parent can unmount it.
 *
 * Props:
 *   userName   {string}  — authenticated user's display name
 *   isNewUser  {boolean} — true → "Welcome to BookBot"
 *                          false → "Welcome back to BookBot"
 *   onDone     {()=>void} — called when the animation is fully complete
 *
 * Accessibility:
 *   - role="status" + aria-live="polite" for screen readers
 *   - prefers-reduced-motion: CSS shortens/removes motion,
 *     JS timing branch matches so the overlay dismisses quickly too
 */

import React, { useEffect, useRef, useState } from 'react';
import './WelcomeTransition.css';

// ─── Detect reduced-motion preference once ────────────────────────────────────
const prefersReducedMotion =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ─── Timing config (ms) ───────────────────────────────────────────────────────
const TIMING = prefersReducedMotion
  ? {
      exitStart:   400,   // start exit after 400ms
      overlayFade: 200,   // overlay fades for 250ms
      totalDone:   650,   // call onDone after this
    }
  : {
      exitStart:   1500,  // content starts moving up
      overlayFade: 700,   // overlay fades out over 350ms (starts at ~2300ms)
      totalDone:   2600,  // call onDone — component unmounts
    };

// ─── Component ────────────────────────────────────────────────────────────────
export default function WelcomeTransition({ userName, isNewUser, onDone }) {
  const [overlayExiting, setOverlayExiting] = useState(false);
  const [contentExiting, setContentExiting] = useState(false);
  const rafRef   = useRef(null);
  const timerRef = useRef([]);

  const safeName = userName && userName.trim() ? userName.trim() : 'there';
  const subtitle = isNewUser
    ? 'Welcome to BookBot'
    : 'Welcome back to BookBot';

  useEffect(() => {
    // Phase 1: content exit (blur + upward drift)
    timerRef.current.push(
      setTimeout(() => setContentExiting(true), TIMING.exitStart)
    );

    // Phase 2: overlay fade-out begins shortly after content exits
    timerRef.current.push(
      setTimeout(
        () => setOverlayExiting(true),
        TIMING.exitStart + TIMING.overlayFade
      )
    );

    // Phase 3: fully done — parent unmounts this component
    timerRef.current.push(
      setTimeout(onDone, TIMING.totalDone)
    );

    return () => {
      timerRef.current.forEach(clearTimeout);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally run once

  return (
    <div
      className={`wt-overlay${overlayExiting ? ' wt-exiting' : ''}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
      aria-label={`${subtitle}, ${safeName}`}
    >
      <div className={`wt-content${contentExiting ? ' wt-content-exit' : ''}`}>
        {/* Wave emoji */}
        <span className="wt-emoji" aria-hidden="true">👋</span>

        {/* Primary heading */}
        <h1 className="wt-heading">
          Hey {safeName}!
        </h1>

        {/* Decorative separator */}
        <div className="wt-divider" aria-hidden="true" />

        {/* Subtitle */}
        <p className="wt-subtitle">{subtitle}</p>
      </div>
    </div>
  );
}
