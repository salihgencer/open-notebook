"use client";

import React from "react";

interface Props {
  content: string;
  outputType: string;
}

export function OutputViewer({ content, outputType }: Props) {
  if (!content) return null;

  return (
    <div className="prose prose-sm max-w-none p-4 border rounded-lg bg-white">
      <div dangerouslySetInnerHTML={{ __html: content }} />
    </div>
  );
}
