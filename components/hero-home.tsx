"use client";

import Link from "next/link";
import RotatingText from "@/components/rotating-text";

export default function HeroHome() {
  return (
    <section>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        {/* Hero content */}
        <div className="py-12 md:py-20">
          {/* Section header */}
          <div className="pb-12 text-center md:pb-20">
            <h1
              className="pb-5 font-nacelle text-4xl font-semibold text-gray-200 md:text-5xl"
              data-aos="fade-up"
            >
              <span className="animate-[gradient_6s_linear_infinite] bg-[linear-gradient(to_right,theme(colors.gray.200),theme(colors.indigo.200),theme(colors.gray.50),theme(colors.indigo.300),theme(colors.gray.200))] bg-[length:200%_auto] bg-clip-text text-transparent">
                Real-Time Physiotherapy with{' '}
              </span>
              <br className="sm:hidden" />
              <RotatingText
                texts={['AI', 'Expertise', 'Care', 'Precision']}
                mainClassName="inline-flex text-white bg-indigo-600 px-3 py-1 sm:mt-0 rounded-lg shadow-lg"
                elementLevelClassName="font-bold"
                staggerDuration={0.05}
                rotationInterval={3000}
              />
            </h1>
            <div className="mx-auto max-w-3xl">
              <p
                className="mb-8 text-xl text-white"
                data-aos="fade-up"
                data-aos-delay={200}
              >
                Accelerate recovery and pain relief with AI-driven custom
                workouts, therapy, and expert nutrition plans
              </p>

              <div className="mx-auto max-w-xs sm:flex sm:max-w-none sm:justify-center">
                <div data-aos="fade-up" data-aos-delay={400}>
                  <Link
                    className="btn group mb-4 w-full bg-gradient-to-t from-red-800 to-red-700 bg-[length:100%_100%] bg-[bottom] text-white shadow-[inset_0px_1px_0px_0px_theme(colors.white/.16)] hover:bg-[length:100%_150%] sm:mb-0 sm:w-auto"
                    href="/signin"
                  >
                    <span className="relative inline-flex items-center">
                      Start Your Journey
                      <span className="ml-1 tracking-normal text-white/50 transition-transform group-hover:translate-x-0.5">
                        -&gt;
                      </span>
                    </span>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
