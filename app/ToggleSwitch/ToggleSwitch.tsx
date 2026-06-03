"use client";

import React, { useEffect, useState } from "react";
import { useAudio } from "@/contexts/AudioContexts";

interface ToggleProps {
  onToggleChange: ({
    isEnabled,
  }: {
    isEnabled: boolean;
  }) => void;
}

export const ToggleSwitch = ({ onToggleChange }: ToggleProps) => {
  const { audiobot, setAudiobot } = useAudio();

  const [isEnabled, setIsEnabled] = useState(audiobot === "on");

  useEffect(() => {
    setIsEnabled(audiobot === "on");
  }, [audiobot]);

  const handleToggle = () => {
    const newEnabled = !isEnabled;
    setIsEnabled(newEnabled);

    if (newEnabled) {
      setAudiobot("on");
    } else {
      setAudiobot("off");
    }

    onToggleChange({ isEnabled: newEnabled });
  };

  return (
    <div className="p-6 flex items-center gap-8">
      {/* Controller Switch */}
      <div className="flex items-center">
        <input
          className="mr-2 mt-[0.3rem] h-3.5 w-8 appearance-none rounded-[0.4375rem] bg-neutral-300 
          before:pointer-events-none before:absolute before:h-3.5 before:w-3.5 before:rounded-full 
          before:bg-transparent before:content-[''] after:absolute after:z-[2] after:-mt-[0.1875rem] 
          after:h-5 after:w-5 after:rounded-full after:border-none after:bg-neutral-100 
          after:shadow-[0_0px_3px_0_rgb(0_0_0_/_7%),_0_2px_2px_0_rgb(0_0_0_/_4%)] 
          after:transition-[background-color_0.2s,transform_0.2s] after:content-[''] 
          checked:bg-primary checked:after:ml-[1.0625rem] 
          checked:after:bg-primary checked:after:shadow-[0_3px_1px_-2px_rgba(0,0,0,0.2),_0_2px_2px_0_rgba(0,0,0,0.14),_0_1px_5px_0_rgba(0,0,0,0.12)] 
          hover:cursor-pointer focus:outline-none"
          type="checkbox"
          role="switch"
          id="controllerSwitch"
          checked={isEnabled}
          onChange={handleToggle}
        />
        <label htmlFor="controllerSwitch" className="inline-block pl-[0.15rem] text-white">
          Enable Audiobot
        </label>
      </div>
    </div>
  );
};
