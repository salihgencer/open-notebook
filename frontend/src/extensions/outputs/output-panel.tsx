"use client";

import React, { useState } from "react";
import { OutputSelector } from "./output-selector";
import { OutputViewer } from "./output-viewer";
import { useI18n } from "../i18n/provider";
import { useAuthContext } from "../auth/auth-provider";

interface Props {
  notebookId: string;
}

export function OutputPanel({ notebookId }: Props) {
  const { t, locale } = useI18n();
  const { accessToken } = useAuthContext();
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!selectedType) return;
    setLoading(true);
    setError("");
    setContent("");

    try {
      const res = await fetch("/api/ext/outputs/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          notebook_id: notebookId,
          output_type: selectedType,
          language: locale,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Generation failed");
      }

      const data = await res.json();
      setContent(data.content);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <OutputSelector onSelect={setSelectedType} selected={selectedType} />
        <button
          onClick={handleGenerate}
          disabled={!selectedType || loading}
          className="px-4 py-1.5 bg-blue-600 text-white rounded-md text-sm disabled:opacity-50"
        >
          {loading ? t("outputs.generating") : t("outputs.generate")}
        </button>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {content && <OutputViewer content={content} outputType={selectedType || ""} />}
    </div>
  );
}
