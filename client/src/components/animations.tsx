import { motion, type Variants, useReducedMotion } from "framer-motion";
import { type ReactNode, useState, useEffect, useRef } from "react";

const fadeInUpVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const fadeInVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const scaleInVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1 },
};

interface AnimationProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export function FadeIn({ children, delay = 0, duration = 0.4, className = "" }: AnimationProps) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <motion.div
      variants={fadeInUpVariants}
      initial={prefersReducedMotion ? "visible" : "hidden"}
      animate="visible"
      transition={{ duration: prefersReducedMotion ? 0 : duration, delay: prefersReducedMotion ? 0 : delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function FadeInSimple({ children, delay = 0, duration = 0.3, className = "" }: AnimationProps) {
  return (
    <motion.div
      variants={fadeInVariants}
      initial="hidden"
      animate="visible"
      transition={{ duration, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function ScaleIn({ children, delay = 0, duration = 0.3, className = "" }: AnimationProps) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <motion.div
      variants={scaleInVariants}
      initial={prefersReducedMotion ? "visible" : "hidden"}
      animate="visible"
      transition={{ duration: prefersReducedMotion ? 0 : duration, delay: prefersReducedMotion ? 0 : delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface SlideInProps extends AnimationProps {
  direction?: "left" | "right" | "up" | "down";
}

export function SlideIn({ children, delay = 0, duration = 0.4, direction = "up", className = "" }: SlideInProps) {
  const offsets = {
    left: { x: -30, y: 0 },
    right: { x: 30, y: 0 },
    up: { x: 0, y: 30 },
    down: { x: 0, y: -30 },
  };
  const offset = offsets[direction];

  return (
    <motion.div
      initial={{ opacity: 0, ...offset }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const staggerContainerVariants: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

const staggerItemVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

interface StaggerProps {
  children: ReactNode;
  className?: string;
}

export function StaggerContainer({ children, className = "" }: StaggerProps) {
  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className = "" }: StaggerProps) {
  return (
    <motion.div variants={staggerItemVariants} className={className}>
      {children}
    </motion.div>
  );
}

export function PageTransition({ children, className = "" }: { children: ReactNode; className?: string }) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <motion.div
      initial={prefersReducedMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: prefersReducedMotion ? 0 : 0.3, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface CountUpProps {
  end: number;
  duration?: number;
  className?: string;
  prefix?: string;
  suffix?: string;
}

export function CountUp({ end, duration = 1.2, className = "", prefix = "", suffix = "" }: CountUpProps) {
  const [current, setCurrent] = useState(0);
  const ref = useRef<number | null>(null);

  useEffect(() => {
    if (typeof end !== "number" || isNaN(end)) return;

    const startTime = performance.now();
    const startValue = 0;

    function animate(now: number) {
      const elapsed = (now - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(startValue + (end - startValue) * eased);
      setCurrent(value);

      if (progress < 1) {
        ref.current = requestAnimationFrame(animate);
      }
    }

    ref.current = requestAnimationFrame(animate);
    return () => {
      if (ref.current) cancelAnimationFrame(ref.current);
    };
  }, [end, duration]);

  return <span className={className}>{prefix}{current}{suffix}</span>;
}

export function HoverCard({ children, className = "" }: { children: ReactNode; className?: string }) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <motion.div
      whileHover={prefersReducedMotion ? {} : { y: -4, transition: { duration: 0.2 } }}
      className={`transition-shadow hover:shadow-lg ${className}`}
    >
      {children}
    </motion.div>
  );
}
