"use client";

import React, { useEffect, useState } from "react";
import { useI18n } from "../i18n/provider";

interface OutputType {
  name: string;
  title: string;
  description: string;
}

interface Props {
  onSelect: (type: string) => void;
  selected: string | null;
}

export function OutputSelector({ onSelect, selected }: Props) {
  const { t } = useI18n();
  const [types, setTypes] = useState<OutputType[]>([]);

  useEffect(() => {
    fetch("/api/ext/outputs/types")
      .then((r) => r.json())
      .then(setTypes)
      .catch(console.error);
  }, []);

  return (
    <div className="flex gap-2 flex-wrap">
      {types.map((type) => (
        <button
          key={type.name}
          onClick={() => onSelect(type.name)}
          className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
            selected === type.name
              ? "bg-blue-600 text-white border-blue-600"
              : "bg-white hover:bg-gray-50 border-gray-300"
          }`}
        >
          {t(`outputs.${type.name}`) || type.title}
        </button>
      ))}
    </div>
  );
}
